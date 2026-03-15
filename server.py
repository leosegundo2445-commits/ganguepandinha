"""
╔══════════════════════════════════════════════════════╗
║   GANGUE DO PANDINHA — Servidor Web                 ║
║   pip install flask                                  ║
║   python server.py                                   ║
║   Site:  http://localhost:5000                       ║
║   Admin: http://localhost:5000/admin                 ║
╚══════════════════════════════════════════════════════╝
"""

from flask import Flask, request, jsonify, render_template_string, abort
import json, os, uuid, datetime, hashlib, socket, sqlite3

app = Flask(__name__)

# ── Config ─────────────────────────────────────────────
# Senha via variável de ambiente ou padrão
ADMIN_SENHA = os.environ.get("ADMIN_SENHA", "pandinha123")
ADMIN_TOKEN = hashlib.sha256(ADMIN_SENHA.encode()).hexdigest()

# Banco SQLite — funciona local e no Render
DB_PATH = os.environ.get("DB_PATH", "candidaturas.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidaturas (
            id TEXT PRIMARY KEY,
            codigo TEXT,
            nick TEXT,
            nivel TEXT,
            discord TEXT,
            horas TEXT,
            tecnica TEXT,
            historico TEXT,
            motivo TEXT,
            conquista TEXT,
            status TEXT DEFAULT 'pendente',
            data TEXT
        )
    """)
    conn.commit()
    return conn

def load_data():
    try:
        conn = get_db()
        rows = conn.execute("SELECT * FROM candidaturas ORDER BY data DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

def save_item(item):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO candidaturas
        (id,codigo,nick,nivel,discord,horas,tecnica,historico,motivo,conquista,status,data)
        VALUES (:id,:codigo,:nick,:nivel,:discord,:horas,:tecnica,:historico,:motivo,:conquista,:status,:data)
    """, item)
    conn.commit()
    conn.close()

def update_status(id_, status):
    conn = get_db()
    conn.execute("UPDATE candidaturas SET status=? WHERE id=?", (status, id_))
    conn.commit()
    conn.close()

def delete_item(id_):
    conn = get_db()
    conn.execute("DELETE FROM candidaturas WHERE id=?", (id_,))
    conn.commit()
    conn.close()

# ══════════════════════════════════════════════════════
#  PÁGINA PRINCIPAL
# ══════════════════════════════════════════════════════
SITE_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Gangue do Pandinha — JujutsuCraft</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --neon:#00f5ff;--neon2:#bf00ff;--neon3:#ff0080;
  --dark:#020408;--card:#071018;--card2:#0a1825;
  --border:rgba(0,245,255,0.2);--text:#c8e8f0;--muted:#4a7080;
}
html{scroll-behavior:smooth}
body{font-family:'Rajdhani',sans-serif;background:var(--dark);color:var(--text);overflow-x:hidden;min-height:100vh}
body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(0,245,255,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,245,255,0.025) 1px,transparent 1px);background-size:44px 44px;pointer-events:none;z-index:0}
body::after{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.06) 2px,rgba(0,0,0,0.06) 4px);pointer-events:none;z-index:1}
.wrap{position:relative;z-index:2;max-width:920px;margin:0 auto;padding:0 24px 80px}

/* HERO */
.hero{text-align:center;padding:64px 20px 48px;opacity:0;animation:hero-in 0.9s cubic-bezier(.22,1,.36,1) 0.1s forwards}
@keyframes hero-in{from{opacity:0;transform:translateY(24px) scale(0.97)}to{opacity:1;transform:none}}
.panda-symbol{font-size:82px;display:block;margin-bottom:18px;filter:drop-shadow(0 0 24px rgba(0,245,255,0.7));animation:float 3s ease-in-out infinite;cursor:pointer;user-select:none;transition:filter 0.3s}
.panda-symbol:hover{animation:none;filter:drop-shadow(0 0 44px rgba(0,245,255,1))}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
.hero-title{font-size:52px;font-weight:700;letter-spacing:4px;text-transform:uppercase;color:#fff;text-shadow:0 0 30px var(--neon),0 0 60px rgba(0,245,255,0.3);line-height:1;animation:glitch 6s infinite}
.hero-title span{color:var(--neon);display:block;font-size:24px;letter-spacing:10px;margin-top:8px}
.hero-sub{font-family:'Share Tech Mono',monospace;color:var(--neon);font-size:12px;letter-spacing:3px;margin-top:14px;opacity:0.6}
.hero-line{width:220px;height:1px;background:linear-gradient(90deg,transparent,var(--neon),transparent);margin:20px auto}
@keyframes glitch{0%,88%,100%{text-shadow:0 0 30px var(--neon),0 0 60px rgba(0,245,255,0.3);transform:none}90%{transform:translate(-2px,0) skewX(-2deg);text-shadow:2px 0 var(--neon3),-2px 0 var(--neon2)}92%{transform:translate(2px,0) skewX(2deg);text-shadow:-2px 0 var(--neon3),2px 0 var(--neon)}94%{transform:translate(-1px,0)}}

/* SEÇÕES */
.section{margin:40px 0;opacity:0;transform:translateY(28px);transition:opacity 0.6s ease,transform 0.6s cubic-bezier(.22,1,.36,1)}
.section.visible{opacity:1;transform:translateY(0)}
.section-title{font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:4px;color:var(--neon);text-transform:uppercase;margin-bottom:16px;display:flex;align-items:center;gap:12px}
.section-title::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,var(--border),transparent)}

/* CARDS */
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:26px;position:relative;overflow:hidden;transition:border-color 0.3s,transform 0.4s cubic-bezier(.34,1.56,.64,1),box-shadow 0.4s;cursor:default}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--neon),transparent)}
.card:hover{border-color:rgba(0,245,255,0.5);transform:translateY(-3px) scale(1.01);box-shadow:0 8px 40px rgba(0,245,255,0.1)}
.lore-text{font-size:15px;line-height:1.9;color:var(--text)}
.lore-text strong{color:var(--neon);font-weight:600}

/* STATS */
.stats-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:22px}
.stat-box{background:rgba(0,245,255,0.05);border:1px solid var(--border);border-radius:8px;padding:18px;text-align:center;transition:transform 0.35s cubic-bezier(.34,1.56,.64,1),background 0.3s;cursor:default}
.stat-box:hover{transform:scale(1.1);background:rgba(0,245,255,0.1)}
.stat-num{font-family:'Share Tech Mono',monospace;font-size:32px;color:var(--neon);display:block;text-shadow:0 0 14px rgba(0,245,255,0.5)}
.stat-label{font-size:10px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-top:4px;display:block}

/* MEMBRO */
.member-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:22px;display:flex;align-items:center;gap:22px;transition:transform 0.4s cubic-bezier(.34,1.56,.64,1),border-color 0.3s,box-shadow 0.4s;position:relative;overflow:hidden;cursor:default}
.member-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--neon2);transition:width 0.3s}
.member-card:hover{border-color:rgba(191,0,255,0.5);transform:scale(1.02) translateX(4px);box-shadow:0 6px 32px rgba(191,0,255,0.12)}
.member-card:hover::before{width:5px}
.member-avatar{width:68px;height:68px;border-radius:50%;background:rgba(191,0,255,0.15);border:2px solid var(--neon2);display:flex;align-items:center;justify-content:center;font-size:30px;flex-shrink:0;box-shadow:0 0 18px rgba(191,0,255,0.3);transition:transform 0.4s cubic-bezier(.34,1.56,.64,1),box-shadow 0.3s}
.member-card:hover .member-avatar{transform:scale(1.15) rotate(6deg);box-shadow:0 0 30px rgba(191,0,255,0.6)}
.member-name{font-size:24px;font-weight:700;color:#fff;letter-spacing:2px}
.member-role{font-family:'Share Tech Mono',monospace;font-size:10px;color:var(--neon2);letter-spacing:3px;margin-top:3px}
.member-tag{display:inline-block;margin-top:9px;padding:4px 12px;background:rgba(191,0,255,0.12);border:1px solid rgba(191,0,255,0.35);border-radius:3px;font-size:11px;color:#d580ff;letter-spacing:1px;transition:background 0.3s,transform 0.3s}
.member-card:hover .member-tag{background:rgba(191,0,255,0.2);transform:scale(1.05)}
.empty-slot{margin-top:12px;font-family:'Share Tech Mono',monospace;font-size:11px;color:var(--muted);text-align:center;padding:22px;border:1px dashed rgba(0,245,255,0.15);border-radius:8px;transition:border-color 0.3s,color 0.3s,transform 0.35s;cursor:default}
.empty-slot:hover{border-color:rgba(0,245,255,0.4);color:var(--neon);transform:scale(1.02)}

/* REGRAS */
.rules-list{list-style:none;display:flex;flex-direction:column;gap:10px}
.rules-list li{display:flex;align-items:flex-start;gap:16px;padding:15px 18px;background:rgba(0,245,255,0.03);border:1px solid var(--border);border-radius:8px;font-size:15px;line-height:1.55;transition:transform 0.35s cubic-bezier(.34,1.56,.64,1),background 0.3s,border-color 0.3s;cursor:default}
.rules-list li:hover{background:rgba(0,245,255,0.08);border-color:rgba(0,245,255,0.4);transform:scale(1.02) translateX(6px)}
.rule-num{font-family:'Share Tech Mono',monospace;color:var(--neon);font-size:12px;min-width:26px;margin-top:2px}

/* FORMULÁRIO */
.form-card{background:var(--card2);border:1px solid var(--border);border-radius:12px;padding:32px;position:relative;overflow:hidden}
.form-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--neon2),transparent)}
.form-grid{display:flex;flex-direction:column;gap:20px}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.form-row-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px}
.field-group label{display:block;font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:3px;color:var(--neon);text-transform:uppercase;margin-bottom:9px}
.field-group input,.field-group select,.field-group textarea{width:100%;background:rgba(0,245,255,0.04);border:1px solid var(--border);border-radius:6px;padding:13px 16px;color:var(--text);font-family:'Rajdhani',sans-serif;font-size:15px;outline:none;transition:border-color 0.25s,background 0.25s,transform 0.3s}
.field-group input:focus,.field-group select:focus,.field-group textarea:focus{border-color:var(--neon);background:rgba(0,245,255,0.08);transform:scale(1.01)}
.field-group select option{background:#0a1520}
.field-group textarea{min-height:100px;resize:vertical}
.field-group input::placeholder,.field-group textarea::placeholder{color:var(--muted)}
.char-count{font-family:'Share Tech Mono',monospace;font-size:10px;color:var(--muted);text-align:right;margin-top:4px}
.radio-group{display:flex;gap:12px;flex-wrap:wrap}
.radio-opt{display:flex;align-items:center;gap:8px;padding:10px 16px;background:rgba(0,245,255,0.04);border:1px solid var(--border);border-radius:6px;cursor:pointer;transition:all 0.25s;font-size:14px;user-select:none}
.radio-opt:hover{border-color:rgba(0,245,255,0.4);background:rgba(0,245,255,0.08)}
.radio-opt.selected{border-color:var(--neon);background:rgba(0,245,255,0.12);color:var(--neon)}
.radio-opt input{display:none}

.btn-apply{width:100%;padding:18px;background:transparent;border:2px solid var(--neon);border-radius:8px;color:var(--neon);font-family:'Rajdhani',sans-serif;font-size:19px;font-weight:700;letter-spacing:4px;text-transform:uppercase;cursor:pointer;position:relative;overflow:hidden;transition:color 0.3s,transform 0.35s cubic-bezier(.34,1.56,.64,1),box-shadow 0.3s;margin-top:8px}
.btn-apply::before{content:'';position:absolute;inset:0;background:var(--neon);transform:scaleX(0);transform-origin:left;transition:transform 0.35s cubic-bezier(.77,0,.18,1);z-index:0}
.btn-apply:hover{color:var(--dark);transform:scale(1.03);box-shadow:0 0 32px rgba(0,245,255,0.45)}
.btn-apply:hover::before{transform:scaleX(1)}
.btn-apply:active{transform:scale(0.97)}
.btn-apply span{position:relative;z-index:1}
.btn-apply:disabled{opacity:0.5;cursor:not-allowed;transform:none}

/* LOADING */
.btn-loading::after{content:'';display:inline-block;width:14px;height:14px;border:2px solid var(--dark);border-top-color:transparent;border-radius:50%;animation:spin 0.7s linear infinite;margin-left:10px;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}

/* SUCESSO */
.success-msg{display:none;text-align:center;padding:40px 32px;background:rgba(0,245,255,0.05);border:1px solid rgba(0,245,255,0.35);border-radius:12px}
.success-msg.show{display:block;animation:pop-in 0.5s cubic-bezier(.34,1.56,.64,1)}
@keyframes pop-in{from{transform:scale(0.7);opacity:0}to{transform:scale(1);opacity:1}}
.success-msg .icon{font-size:52px;display:block;margin-bottom:16px}
.success-msg h3{color:var(--neon);font-size:26px;letter-spacing:4px;margin-bottom:12px}
.success-msg p{color:var(--muted);font-size:13px;font-family:'Share Tech Mono',monospace;line-height:1.9}
.success-msg .cod{color:var(--neon);font-weight:bold;font-size:15px}

/* ERRO */
.error-msg{display:none;padding:14px 18px;background:rgba(255,0,128,0.08);border:1px solid rgba(255,0,128,0.4);border-radius:6px;color:#ff6699;font-family:'Share Tech Mono',monospace;font-size:12px;letter-spacing:1px;margin-top:12px}
.error-msg.show{display:block;animation:pop-in 0.3s ease}

/* RIPPLE */
.ripple-host{position:relative;overflow:hidden}
.ripple{position:absolute;border-radius:50%;background:rgba(0,245,255,0.15);transform:scale(0);animation:ripple-out 0.65s linear;pointer-events:none}
@keyframes ripple-out{to{transform:scale(4);opacity:0}}

/* FOOTER */
.footer{text-align:center;padding:40px 0 20px;font-family:'Share Tech Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:2px;border-top:1px solid var(--border);margin-top:20px}
.footer span{color:var(--neon)}
.footer a{color:var(--muted);text-decoration:none;transition:color 0.2s}
.footer a:hover{color:var(--neon)}

@media(max-width:640px){
  .hero-title{font-size:34px}
  .stats-grid{grid-template-columns:1fr 1fr}
  .form-row,.form-row-3{grid-template-columns:1fr}
  .member-card{flex-direction:column;text-align:center}
}
</style>
</head>
<body>
<div class="wrap">

  <div class="hero">
    <span class="panda-symbol" id="panda">🐼</span>
    <h1 class="hero-title">GANGUE DO PANDINHA<span>JUJUTSU CRAFT</span></h1>
    <p class="hero-sub">// servidor de roleplay &bull; maldições &bull; poder ilimitado //</p>
    <div class="hero-line"></div>
  </div>

  <!-- LORE -->
  <div class="section">
    <div class="section-title">// lore da gangue</div>
    <div class="card ripple-host">
      <p class="lore-text">
        Nas sombras do servidor, quando os investigadores do Jujutsu dormem,
        <strong>o Pandinha abriu os olhos.</strong><br><br>
        Dizem que foi durante o <strong>Grande Torneio das Maldições</strong> que ele surgiu —
        um feiticeiro sem clã, sem passado, capaz de dominar técnicas que nenhum mestre
        ousava ensinar. Com um único gesto, formou a gangue que hoje todo o servidor teme e respeita.<br><br>
        A <strong>Gangue do Pandinha</strong> não é apenas uma aliança — é um <strong>domínio expandido</strong>.
        Quem entra, entra de alma. Quem trai, encontra o vazio absoluto.
        Nosso código: <strong>lealdade, poder, e nunca recuar.</strong>
      </p>
      <div class="stats-grid">
        <div class="stat-box ripple-host"><span class="stat-num" id="stat-lider">01</span><span class="stat-label">Líder Supremo</span></div>
        <div class="stat-box ripple-host"><span class="stat-num" id="stat-cands">...</span><span class="stat-label">Candidatos</span></div>
        <div class="stat-box ripple-host"><span class="stat-num">&#x221e;</span><span class="stat-label">Poder Cursed</span></div>
      </div>
    </div>
  </div>

  <!-- MEMBROS -->
  <div class="section">
    <div class="section-title">// membros ativos</div>
    <div class="member-card ripple-host">
      <div class="member-avatar">🐼</div>
      <div>
        <div class="member-name">PANDINHA</div>
        <div class="member-role">// líder supremo &bull; fundador</div>
        <div class="member-tag">Técnica Cursed: Domínio do Panda Invertido</div>
      </div>
    </div>
    <div class="empty-slot">... aguardando novos guerreiros ...</div>
  </div>

  <!-- REGRAS -->
  <div class="section">
    <div class="section-title">// código de conduta</div>
    <div class="card" style="padding:20px">
      <ul class="rules-list">
        <li class="ripple-host"><span class="rule-num">01</span><span>Lealdade total ao Pandinha e aos membros. Traição é punida com expulsão imediata.</span></li>
        <li class="ripple-host"><span class="rule-num">02</span><span>Participar das missões e eventos do clã. Inativo +7 dias sem aviso é removido.</span></li>
        <li class="ripple-host"><span class="rule-num">03</span><span>Respeitar as regras do servidor JujutsuCraft. Não damos vergonha pro Pandinha.</span></li>
        <li class="ripple-host"><span class="rule-num">04</span><span>Conflitos internos se resolvem dentro da gangue. Nada de drama público no chat.</span></li>
        <li class="ripple-host"><span class="rule-num">05</span><span>Ajudar membros mais novos. Crescemos juntos ou não crescemos.</span></li>
        <li class="ripple-host"><span class="rule-num">06</span><span>Proibido atacar membro da gangue. PvP interno só em duelos combinados.</span></li>
      </ul>
    </div>
  </div>

  <!-- FORMULÁRIO -->
  <div class="section">
    <div class="section-title">// solicitar entrada na gangue</div>
    <div class="form-card" id="form-card">
      <div id="the-form">
        <div class="form-grid">

          <div class="form-row">
            <div class="field-group">
              <label>Nick no servidor *</label>
              <input type="text" id="nick" placeholder="SeuNickAqui" maxlength="30"/>
            </div>
            <div class="field-group">
              <label>Nível atual *</label>
              <input type="number" id="nivel" placeholder="Ex: 47" min="1" max="9999"/>
            </div>
          </div>

          <div class="form-row">
            <div class="field-group">
              <label>Discord (opcional)</label>
              <input type="text" id="discord" placeholder="usuario#0000 ou @usuario"/>
            </div>
            <div class="field-group">
              <label>Horas de jogo por semana</label>
              <select id="horas">
                <option value="">Selecione...</option>
                <option>Menos de 5h</option>
                <option>5h a 15h</option>
                <option>15h a 30h</option>
                <option>Mais de 30h</option>
              </select>
            </div>
          </div>

          <div class="field-group">
            <label>Técnica maldita principal *</label>
            <select id="tecnica">
              <option value="">Selecione sua técnica...</option>
              <option>Transmutação do Infinito</option>
              <option>Olho de Serpente e Olhos de Bovino</option>
              <option>Chama Divina</option>
              <option>Técnica da Sombra das Dez Sombras</option>
              <option>Sangue Maldito</option>
              <option>Domínio Expansivo</option>
              <option>Inversão Cursed</option>
              <option>Outra (descreva abaixo)</option>
            </select>
          </div>

          <div class="field-group">
            <label>Já foi de outra gangue? *</label>
            <div class="radio-group" id="historico-group">
              <label class="radio-opt ripple-host" onclick="selectRadio(this,'historico','livre')">
                <input type="radio" name="hist" value="livre"> Não, sou livre
              </label>
              <label class="radio-opt ripple-host" onclick="selectRadio(this,'historico','saiu')">
                <input type="radio" name="hist" value="saiu"> Saí pacificamente
              </label>
              <label class="radio-opt ripple-host" onclick="selectRadio(this,'historico','expulso')">
                <input type="radio" name="hist" value="expulso"> Fui expulso
              </label>
              <label class="radio-opt ripple-host" onclick="selectRadio(this,'historico','nao-diz')">
                <input type="radio" name="hist" value="nao-diz"> Prefiro não dizer
              </label>
            </div>
          </div>

          <div class="field-group">
            <label>Por que quer entrar na gangue? *</label>
            <textarea id="motivo" placeholder="Me convença em suas palavras... O Pandinha está lendo." maxlength="400" oninput="updateCount(this,'motivo-count')"></textarea>
            <div class="char-count"><span id="motivo-count">0</span>/400</div>
          </div>

          <div class="field-group">
            <label>Qual sua maior conquista no servidor?</label>
            <textarea id="conquista" placeholder="Opcional, mas impressiona..." maxlength="250" oninput="updateCount(this,'conquista-count')"></textarea>
            <div class="char-count"><span id="conquista-count">0</span>/250</div>
          </div>

          <button class="btn-apply ripple-host" id="btn-send" onclick="enviar()">
            <span id="btn-text">⚡ Solicitar Entrada ⚡</span>
          </button>

          <div class="error-msg" id="error-msg">⚠ Preencha todos os campos obrigatórios (*)</div>
        </div>
      </div>

      <div class="success-msg" id="success">
        <span class="icon">🐼</span>
        <h3>SOLICITAÇÃO ENVIADA!</h3>
        <p>
          O Pandinha foi notificado.<br>
          Aguarde o contato no servidor ou Discord.<br><br>
          Código da candidatura:<br>
          <span class="cod" id="cod-display"></span>
        </p>
      </div>
    </div>
  </div>

  <div class="footer">
    <span>GANGUE DO PANDINHA</span> &bull; JUJUTSU CRAFT RP<br>
    <span style="opacity:0.3">// nenhuma maldição nos detém //</span>
    &nbsp;&nbsp;&bull;&nbsp;&nbsp;
    <a href="/admin">painel admin</a>
  </div>
</div>

<script>
// Ripple
document.querySelectorAll('.ripple-host').forEach(function(el){
  el.addEventListener('click',function(e){
    var r=document.createElement('span');
    r.className='ripple';
    var rect=el.getBoundingClientRect();
    var sz=Math.max(rect.width,rect.height);
    r.style.cssText='width:'+sz+'px;height:'+sz+'px;left:'+(e.clientX-rect.left-sz/2)+'px;top:'+(e.clientY-rect.top-sz/2)+'px;';
    el.appendChild(r);
    setTimeout(function(){r.remove();},700);
  });
});

// Scroll reveal
var io=new IntersectionObserver(function(entries){
  entries.forEach(function(entry,i){
    if(entry.isIntersecting){
      setTimeout(function(){entry.target.classList.add('visible');},i*70);
      io.unobserve(entry.target);
    }
  });
},{threshold:0.06});
document.querySelectorAll('.section').forEach(function(s){io.observe(s);});

// Panda gira
var panda=document.getElementById('panda');
var rot=0;
panda.addEventListener('click',function(){
  rot+=360;
  panda.style.transition='transform 0.7s cubic-bezier(.34,1.56,.64,1),filter 0.3s';
  panda.style.animation='none';
  panda.style.transform='rotate('+rot+'deg) scale(1.35)';
  setTimeout(function(){panda.style.transform='rotate('+rot+'deg) scale(1)';},700);
});

// Radio custom
var radios={};
function selectRadio(el,field,val){
  radios[field]=val;
  document.querySelectorAll('#historico-group .radio-opt').forEach(function(o){o.classList.remove('selected');});
  el.classList.add('selected');
}

// Contador de chars
function updateCount(el,id){
  document.getElementById(id).textContent=el.value.length;
}

// Carregar stats
fetch('/api/stats').then(function(r){return r.json();}).then(function(d){
  document.getElementById('stat-cands').textContent=d.total||'0';
});

// Envio
function enviar(){
  var nick=document.getElementById('nick').value.trim();
  var nivel=document.getElementById('nivel').value.trim();
  var tecnica=document.getElementById('tecnica').value;
  var motivo=document.getElementById('motivo').value.trim();
  var historico=radios['historico']||'';

  var ok=true;
  [document.getElementById('nick'),document.getElementById('nivel'),document.getElementById('tecnica'),document.getElementById('motivo')].forEach(function(el){
    if(!el.value.trim()){
      el.style.borderColor='rgba(255,0,128,0.9)';
      el.style.background='rgba(255,0,128,0.06)';
      setTimeout(function(){el.style.borderColor='';el.style.background='';},2500);
      ok=false;
    }
  });
  if(!historico){
    document.querySelectorAll('#historico-group .radio-opt').forEach(function(o){
      o.style.borderColor='rgba(255,0,128,0.7)';
      setTimeout(function(){o.style.borderColor='';},2500);
    });
    ok=false;
  }
  if(!ok){
    var err=document.getElementById('error-msg');
    err.classList.add('show');
    setTimeout(function(){err.classList.remove('show');},3000);
    return;
  }

  var btn=document.getElementById('btn-send');
  var txt=document.getElementById('btn-text');
  btn.disabled=true;
  btn.classList.add('btn-loading');
  txt.textContent='Enviando...';

  fetch('/api/candidatura',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      nick:nick, nivel:nivel,
      discord:document.getElementById('discord').value.trim(),
      horas:document.getElementById('horas').value,
      tecnica:tecnica, historico:historico,
      motivo:motivo,
      conquista:document.getElementById('conquista').value.trim()
    })
  })
  .then(function(r){return r.json();})
  .then(function(d){
    document.getElementById('the-form').style.display='none';
    document.getElementById('success').classList.add('show');
    document.getElementById('cod-display').textContent=d.codigo;
  })
  .catch(function(){
    btn.disabled=false;
    btn.classList.remove('btn-loading');
    txt.textContent='⚡ Solicitar Entrada ⚡';
    alert('Erro ao enviar. Tenta de novo!');
  });
}
</script>
</body>
</html>"""

# ══════════════════════════════════════════════════════
#  PAINEL ADMIN
# ══════════════════════════════════════════════════════
ADMIN_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Admin — Gangue do Pandinha</title>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--neon:#00f5ff;--neon2:#bf00ff;--dark:#020408;--card:#071018;--border:rgba(0,245,255,0.2);--text:#c8e8f0;--muted:#4a7080;--green:#00cc55;--red:#ff3355}
body{font-family:'Rajdhani',sans-serif;background:var(--dark);color:var(--text);min-height:100vh}
body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(0,245,255,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,245,255,0.025) 1px,transparent 1px);background-size:44px 44px;pointer-events:none;z-index:0}
.wrap{position:relative;z-index:1;max-width:1100px;margin:0 auto;padding:30px 24px 60px}

/* LOGIN */
.login-box{max-width:400px;margin:80px auto;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:40px;text-align:center;position:relative;overflow:hidden}
.login-box::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--neon),transparent)}
.login-box h2{font-size:22px;letter-spacing:3px;color:#fff;margin-bottom:6px}
.login-box p{font-family:'Share Tech Mono',monospace;font-size:11px;color:var(--muted);margin-bottom:26px}
.login-box input{width:100%;background:rgba(0,245,255,0.04);border:1px solid var(--border);border-radius:6px;padding:13px 16px;color:var(--text);font-family:'Rajdhani',sans-serif;font-size:15px;outline:none;margin-bottom:14px;transition:border-color 0.2s}
.login-box input:focus{border-color:var(--neon)}
.btn-login{width:100%;padding:14px;background:transparent;border:2px solid var(--neon);border-radius:6px;color:var(--neon);font-family:'Rajdhani',sans-serif;font-size:16px;font-weight:700;letter-spacing:3px;cursor:pointer;transition:all 0.3s;position:relative;overflow:hidden}
.btn-login::before{content:'';position:absolute;inset:0;background:var(--neon);transform:scaleX(0);transform-origin:left;transition:transform 0.3s;z-index:0}
.btn-login:hover{color:var(--dark)}
.btn-login:hover::before{transform:scaleX(1)}
.btn-login span{position:relative;z-index:1}
.login-err{color:#ff3355;font-family:'Share Tech Mono',monospace;font-size:11px;margin-top:10px;display:none}

/* HEADER ADMIN */
.admin-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:28px;padding-bottom:16px;border-bottom:1px solid var(--border)}
.admin-header h1{font-size:26px;font-weight:700;letter-spacing:3px;color:#fff}
.admin-header h1 span{color:var(--neon)}
.btn-back{font-family:'Share Tech Mono',monospace;font-size:11px;color:var(--muted);text-decoration:none;border:1px solid var(--border);padding:8px 14px;border-radius:6px;transition:all 0.2s}
.btn-back:hover{color:var(--neon);border-color:var(--neon)}
.btn-logout{font-family:'Share Tech Mono',monospace;font-size:11px;color:var(--red);text-decoration:none;border:1px solid rgba(255,51,85,0.3);padding:8px 14px;border-radius:6px;cursor:pointer;background:transparent;transition:all 0.2s}
.btn-logout:hover{background:rgba(255,51,85,0.1)}

/* STATS */
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px;text-align:center;transition:transform 0.3s}
.stat-card:hover{transform:translateY(-3px)}
.stat-num{font-family:'Share Tech Mono',monospace;font-size:32px;color:var(--neon);display:block;text-shadow:0 0 12px rgba(0,245,255,0.4)}
.stat-label{font-size:11px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-top:4px;display:block}

/* FILTROS */
.filters{display:flex;gap:10px;margin-bottom:18px;flex-wrap:wrap;align-items:center}
.filter-btn{font-family:'Share Tech Mono',monospace;font-size:11px;padding:8px 16px;border:1px solid var(--border);border-radius:6px;background:transparent;color:var(--muted);cursor:pointer;transition:all 0.2s;letter-spacing:1px}
.filter-btn.active,.filter-btn:hover{border-color:var(--neon);color:var(--neon);background:rgba(0,245,255,0.07)}
.search-input{font-family:'Share Tech Mono',monospace;font-size:12px;padding:8px 14px;background:rgba(0,245,255,0.04);border:1px solid var(--border);border-radius:6px;color:var(--text);outline:none;width:220px;transition:border-color 0.2s}
.search-input:focus{border-color:var(--neon)}

/* TABELA */
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px}
thead tr{border-bottom:1px solid var(--border)}
th{font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;color:var(--neon);padding:12px 16px;text-align:left;text-transform:uppercase;white-space:nowrap}
tbody tr{border-bottom:1px solid rgba(0,245,255,0.06);transition:background 0.2s,transform 0.2s;cursor:pointer}
tbody tr:hover{background:rgba(0,245,255,0.04);transform:translateX(3px)}
td{padding:14px 16px;vertical-align:top}
.nick{font-weight:700;color:#fff;font-size:15px}
.nivel{font-family:'Share Tech Mono',monospace;color:var(--neon);font-size:13px}
.tecnica{font-size:12px;color:var(--text)}
.data{font-family:'Share Tech Mono',monospace;font-size:11px;color:var(--muted)}
.badge{display:inline-block;padding:3px 10px;border-radius:3px;font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:1px}
.badge-pending{background:rgba(201,168,76,0.15);border:1px solid rgba(201,168,76,0.4);color:#c9a84c}
.badge-aceito{background:rgba(0,204,85,0.12);border:1px solid rgba(0,204,85,0.4);color:var(--green)}
.badge-recusado{background:rgba(255,51,85,0.12);border:1px solid rgba(255,51,85,0.4);color:var(--red)}
.actions{display:flex;gap:6px}
.btn-aceitar,.btn-recusar,.btn-del{font-family:'Share Tech Mono',monospace;font-size:10px;padding:5px 10px;border-radius:4px;cursor:pointer;border:1px solid;transition:all 0.2s;letter-spacing:1px}
.btn-aceitar{color:var(--green);border-color:rgba(0,204,85,0.4);background:rgba(0,204,85,0.07)}
.btn-aceitar:hover{background:rgba(0,204,85,0.18)}
.btn-recusar{color:var(--red);border-color:rgba(255,51,85,0.4);background:rgba(255,51,85,0.07)}
.btn-recusar:hover{background:rgba(255,51,85,0.18)}
.btn-del{color:var(--muted);border-color:var(--border);background:transparent}
.btn-del:hover{color:var(--red);border-color:rgba(255,51,85,0.4)}
.empty-table{text-align:center;padding:50px;font-family:'Share Tech Mono',monospace;font-size:12px;color:var(--muted)}

/* MODAL */
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:100;align-items:center;justify-content:center}
.modal-bg.show{display:flex}
.modal{background:#0a1520;border:1px solid var(--border);border-radius:14px;padding:32px;max-width:600px;width:90%;max-height:85vh;overflow-y:auto;position:relative}
.modal::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--neon2),transparent)}
.modal h3{font-size:20px;letter-spacing:2px;color:#fff;margin-bottom:20px}
.modal-close{position:absolute;top:16px;right:16px;background:transparent;border:none;color:var(--muted);font-size:20px;cursor:pointer;transition:color 0.2s;line-height:1}
.modal-close:hover{color:var(--red)}
.detail-row{display:flex;gap:12px;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid rgba(0,245,255,0.07)}
.detail-row:last-child{border-bottom:none;margin-bottom:0}
.detail-label{font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;color:var(--neon);min-width:120px;margin-top:2px}
.detail-val{font-size:14px;color:var(--text);line-height:1.6}
.modal-actions{display:flex;gap:10px;margin-top:24px;padding-top:18px;border-top:1px solid var(--border)}
.modal-btn{flex:1;padding:12px;border-radius:6px;font-family:'Rajdhani',sans-serif;font-size:15px;font-weight:700;letter-spacing:2px;cursor:pointer;border:2px solid;transition:all 0.25s}
.modal-aceitar{color:var(--green);border-color:var(--green);background:rgba(0,204,85,0.07)}
.modal-aceitar:hover{background:rgba(0,204,85,0.2)}
.modal-recusar{color:var(--red);border-color:var(--red);background:rgba(255,51,85,0.07)}
.modal-recusar:hover{background:rgba(255,51,85,0.2)}

@media(max-width:700px){.stats-row{grid-template-columns:1fr 1fr}.filters{flex-direction:column}.search-input{width:100%}}
</style>
</head>
<body>
<div class="wrap">

  <!-- LOGIN -->
  <div id="login-section">
    <div class="login-box">
      <h2>🐼 ADMIN PANEL</h2>
      <p>// gangue do pandinha // acesso restrito //</p>
      <input type="password" id="senha-input" placeholder="Senha de acesso" onkeydown="if(event.key==='Enter')fazerLogin()"/>
      <button class="btn-login" onclick="fazerLogin()"><span>ENTRAR</span></button>
      <p class="login-err" id="login-err">⚠ Senha incorreta</p>
    </div>
  </div>

  <!-- PAINEL -->
  <div id="painel" style="display:none">
    <div class="admin-header">
      <h1>🐼 ADMIN <span>// CANDIDATURAS</span></h1>
      <div style="display:flex;gap:10px;align-items:center">
        <a href="/" class="btn-back">← site</a>
        <button class="btn-logout" onclick="logout()">sair</button>
      </div>
    </div>

    <div class="stats-row" id="stats-row">
      <div class="stat-card"><span class="stat-num" id="s-total">0</span><span class="stat-label">Total</span></div>
      <div class="stat-card"><span class="stat-num" id="s-pend" style="color:#c9a84c">0</span><span class="stat-label">Pendentes</span></div>
      <div class="stat-card"><span class="stat-num" id="s-aceit" style="color:var(--green)">0</span><span class="stat-label">Aceitos</span></div>
      <div class="stat-card"><span class="stat-num" id="s-rec" style="color:var(--red)">0</span><span class="stat-label">Recusados</span></div>
    </div>

    <div class="filters">
      <button class="filter-btn active" onclick="filtrar('todos',this)">TODOS</button>
      <button class="filter-btn" onclick="filtrar('pendente',this)">PENDENTES</button>
      <button class="filter-btn" onclick="filtrar('aceito',this)">ACEITOS</button>
      <button class="filter-btn" onclick="filtrar('recusado',this)">RECUSADOS</button>
      <input class="search-input" id="search" placeholder="Buscar nick..." oninput="renderTabela()"/>
      <button class="filter-btn" onclick="exportarCSV()" style="margin-left:auto">⬇ CSV</button>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Nick</th>
            <th>Nível</th>
            <th>Técnica</th>
            <th>Discord</th>
            <th>Data</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody id="tabela-body"></tbody>
      </table>
      <div class="empty-table" id="empty-msg" style="display:none">Nenhuma candidatura encontrada.</div>
    </div>
  </div>
</div>

<!-- MODAL DETALHES -->
<div class="modal-bg" id="modal-bg" onclick="if(event.target===this)fecharModal()">
  <div class="modal">
    <button class="modal-close" onclick="fecharModal()">✕</button>
    <h3 id="modal-title">Candidatura</h3>
    <div id="modal-body"></div>
    <div class="modal-actions" id="modal-actions"></div>
  </div>
</div>

<script>
var TOKEN='';
var DADOS=[];
var FILTRO='todos';
var MODAL_ID='';

function fazerLogin(){
  var s=document.getElementById('senha-input').value;
  fetch('/api/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({senha:s})})
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.ok){
      TOKEN=d.token;
      document.getElementById('login-section').style.display='none';
      document.getElementById('painel').style.display='block';
      carregar();
    } else {
      var e=document.getElementById('login-err');
      e.style.display='block';
      setTimeout(function(){e.style.display='none';},2500);
    }
  });
}

function logout(){
  TOKEN='';DADOS=[];
  document.getElementById('painel').style.display='none';
  document.getElementById('login-section').style.display='block';
  document.getElementById('senha-input').value='';
}

function carregar(){
  fetch('/api/admin/candidaturas',{headers:{'X-Token':TOKEN}})
  .then(function(r){return r.json();})
  .then(function(d){
    DADOS=d.candidaturas||[];
    atualizarStats();
    renderTabela();
  });
}

function atualizarStats(){
  document.getElementById('s-total').textContent=DADOS.length;
  document.getElementById('s-pend').textContent=DADOS.filter(function(c){return c.status==='pendente';}).length;
  document.getElementById('s-aceit').textContent=DADOS.filter(function(c){return c.status==='aceito';}).length;
  document.getElementById('s-rec').textContent=DADOS.filter(function(c){return c.status==='recusado';}).length;
}

function filtrar(f,btn){
  FILTRO=f;
  document.querySelectorAll('.filter-btn').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');
  renderTabela();
}

function renderTabela(){
  var busca=document.getElementById('search').value.toLowerCase();
  var lista=DADOS.filter(function(c){
    if(FILTRO!=='todos'&&c.status!==FILTRO) return false;
    if(busca&&c.nick.toLowerCase().indexOf(busca)===-1) return false;
    return true;
  }).sort(function(a,b){return new Date(b.data)-new Date(a.data);});

  var tb=document.getElementById('tabela-body');
  tb.innerHTML='';
  document.getElementById('empty-msg').style.display=lista.length?'none':'block';

  lista.forEach(function(c){
    var tr=document.createElement('tr');
    var badge=c.status==='pendente'?'badge-pending':c.status==='aceito'?'badge-aceito':'badge-recusado';
    var label=c.status==='pendente'?'PENDENTE':c.status==='aceito'?'ACEITO':'RECUSADO';
    var d=new Date(c.data);
    var ds=d.getDate().toString().padStart(2,'0')+'/'+(d.getMonth()+1).toString().padStart(2,'0')+' '+d.getHours().toString().padStart(2,'0')+':'+d.getMinutes().toString().padStart(2,'0');
    tr.innerHTML='<td><span class="nick">'+c.nick+'</span></td>'
      +'<td><span class="nivel">Lv'+c.nivel+'</span></td>'
      +'<td><span class="tecnica">'+c.tecnica+'</span></td>'
      +'<td><span class="data">'+(c.discord||'—')+'</span></td>'
      +'<td><span class="data">'+ds+'</span></td>'
      +'<td><span class="badge '+badge+'">'+label+'</span></td>'
      +'<td><div class="actions">'
        +(c.status!=='aceito'?'<button class="btn-aceitar" onclick="mudarStatus(\''+c.id+'\',\'aceito\',event)">✓ ACE</button>':'')
        +(c.status!=='recusado'?'<button class="btn-recusar" onclick="mudarStatus(\''+c.id+'\',\'recusado\',event)">✗ REC</button>':'')
        +'<button class="btn-del" onclick="deletar(\''+c.id+'\',event)">🗑</button>'
      +'</div></td>';
    tr.onclick=function(){abrirModal(c.id);};
    tb.appendChild(tr);
  });
}

function mudarStatus(id,status,e){
  e.stopPropagation();
  fetch('/api/admin/status',{method:'POST',headers:{'Content-Type':'application/json','X-Token':TOKEN},body:JSON.stringify({id:id,status:status})})
  .then(function(){carregar();if(MODAL_ID===id)abrirModal(id);});
}

function deletar(id,e){
  e.stopPropagation();
  if(!confirm('Deletar candidatura?'))return;
  fetch('/api/admin/deletar',{method:'POST',headers:{'Content-Type':'application/json','X-Token':TOKEN},body:JSON.stringify({id:id})})
  .then(function(){carregar();if(MODAL_ID===id)fecharModal();});
}

function abrirModal(id){
  MODAL_ID=id;
  var c=DADOS.find(function(x){return x.id===id;});
  if(!c)return;
  document.getElementById('modal-title').textContent='Candidatura — '+c.nick;
  var campos=[
    ['Nick',c.nick],['Nível','Lv '+c.nivel],
    ['Discord',c.discord||'—'],['Horas/semana',c.horas||'—'],
    ['Técnica',c.tecnica],['Histórico',c.historico],
    ['Motivo',c.motivo],['Conquista',c.conquista||'—'],
    ['Status',c.status.toUpperCase()],['Código',c.codigo],
    ['Data',new Date(c.data).toLocaleString('pt-BR')]
  ];
  document.getElementById('modal-body').innerHTML=campos.map(function(r){
    return '<div class="detail-row"><span class="detail-label">'+r[0]+'</span><span class="detail-val">'+r[1]+'</span></div>';
  }).join('');
  var acts='';
  if(c.status!=='aceito') acts+='<button class="modal-btn modal-aceitar" onclick="mudarStatus(\''+c.id+'\',\'aceito\',event)">✓ ACEITAR</button>';
  if(c.status!=='recusado') acts+='<button class="modal-btn modal-recusar" onclick="mudarStatus(\''+c.id+'\',\'recusado\',event)">✗ RECUSAR</button>';
  document.getElementById('modal-actions').innerHTML=acts;
  document.getElementById('modal-bg').classList.add('show');
}

function fecharModal(){
  document.getElementById('modal-bg').classList.remove('show');
  MODAL_ID='';
}

function exportarCSV(){
  var linhas=[['Nick','Nivel','Discord','Horas','Tecnica','Historico','Motivo','Conquista','Status','Codigo','Data']];
  DADOS.forEach(function(c){
    linhas.push([c.nick,c.nivel,c.discord||'',c.horas||'',c.tecnica,c.historico,c.motivo,c.conquista||'',c.status,c.codigo,new Date(c.data).toLocaleString('pt-BR')]);
  });
  var csv=linhas.map(function(r){return r.map(function(v){return '"'+(v||'').toString().replace(/"/g,'""')+'"';}).join(',');}).join('\n');
  var a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,'+encodeURIComponent('\uFEFF'+csv);
  a.download='candidaturas.csv';
  a.click();
}

document.addEventListener('keydown',function(e){if(e.key==='Escape')fecharModal();});
</script>
</body>
</html>"""

# ══════════════════════════════════════════════════════
#  ROTAS
# ══════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template_string(SITE_HTML)

@app.route("/admin")
def admin():
    return render_template_string(ADMIN_HTML)

@app.route("/api/stats")
def stats():
    data = load_data()
    return jsonify({"total": len(data)})

@app.route("/api/candidatura", methods=["POST"])
def candidatura():
    d = request.json or {}
    if not all([d.get("nick"), d.get("nivel"), d.get("tecnica"), d.get("motivo")]):
        return jsonify({"erro": "Campos obrigatórios faltando"}), 400

    cod = "PND-" + uuid.uuid4().hex[:6].upper()
    item = {
        "id":        uuid.uuid4().hex,
        "codigo":    cod,
        "nick":      d.get("nick", "").strip(),
        "nivel":     d.get("nivel", "").strip(),
        "discord":   d.get("discord", "").strip(),
        "horas":     d.get("horas", "").strip(),
        "tecnica":   d.get("tecnica", "").strip(),
        "historico": d.get("historico", "").strip(),
        "motivo":    d.get("motivo", "").strip(),
        "conquista": d.get("conquista", "").strip(),
        "status":    "pendente",
        "data":      datetime.datetime.now().isoformat(),
    }
    save_item(item)
    print(f"[NOVA CANDIDATURA] {item['nick']} (Lv{item['nivel']}) — {cod}")
    return jsonify({"ok": True, "codigo": cod})

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    d = request.json or {}
    h = hashlib.sha256(d.get("senha", "").encode()).hexdigest()
    if h == ADMIN_TOKEN:
        return jsonify({"ok": True, "token": ADMIN_TOKEN})
    return jsonify({"ok": False})

def check_token():
    return request.headers.get("X-Token") == ADMIN_TOKEN

@app.route("/api/admin/candidaturas")
def admin_cands():
    if not check_token(): abort(403)
    return jsonify({"candidaturas": load_data()})

@app.route("/api/admin/status", methods=["POST"])
def admin_status():
    if not check_token(): abort(403)
    d = request.json or {}
    update_status(d.get("id"), d.get("status", "pendente"))
    return jsonify({"ok": True})

@app.route("/api/admin/deletar", methods=["POST"])
def admin_deletar():
    if not check_token(): abort(403)
    d = request.json or {}
    delete_item(d.get("id"))
    return jsonify({"ok": True})

# ══════════════════════════════════════════════════════
#  START
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    host = "0.0.0.0"
    port = 5000

    try:
        s_tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_tmp.connect(("8.8.8.8", 80))
        ip_local = s_tmp.getsockname()[0]
        s_tmp.close()
    except Exception:
        ip_local = "127.0.0.1"

    print("\n" + "="*52)
    print("  GANGUE DO PANDINHA — SERVIDOR RODANDO!")
    print("="*52)
    print(f"  Site:   http://localhost:{port}")
    print(f"  Site:   http://{ip_local}:{port}")
    print(f"  Admin:  http://localhost:{port}/admin")
    print(f"  Senha:  {ADMIN_SENHA}")
    print("="*52 + "\n")

    app.run(host=host, port=port, debug=False)
