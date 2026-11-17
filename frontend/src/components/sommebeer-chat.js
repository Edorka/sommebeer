import { LitElement, css, html, nothing } from 'lit';
import './md-block.js';

/**
 * sommebeer-chat — the whole tavern in one custom element.
 * All styling lives in this component's shadow root (embedded via `static styles`).
 */
export class SommebeerChat extends LitElement {
  static properties = {
    lines: { state: true },
    draft: { state: true },
    busy: { state: true },
    error: { state: true },
  };

  constructor() {
    super();
    this.lines = [];
    this.draft = '';
    this.busy = false;
    this.error = null;
  }

  static styles = css`
    :host {
      /* palette — scoped tokens for both this element and md-block's shadow */
      --paper: #f7f0e3;
      --paper-deep: #efe4d0;
      --ink: #3b2f23;
      --ink-soft: #7a6a55;
      --amber: #b3772f;
      --amber-deep: #8b5a1f;
      --card: #fffdf7;
      --radius: 14px;

      /* layout instead of the old body{} rules */
      display: block;
      font-family: 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif;
      line-height: 1.55;
      color: var(--ink);
    }

    * {
      box-sizing: border-box;
    }

    .wrap {
      max-width: 640px;
      margin: 0 auto;
      padding: 2rem 1rem;
      display: flex;
      flex-direction: column;
      justify-content: center;
      min-height: 100vh;
    }

    header {
      text-align: center;
      margin-bottom: 1rem;
    }
    h1 {
      margin: 0;
      font-weight: 700;
      color: var(--amber-deep);
      font-size: 2rem;
      letter-spacing: 0.02em;
    }
    .tagline {
      margin: 0.25rem 0 0;
      color: var(--ink-soft);
      font-style: italic;
    }

    /* the conversation area — capped so it sits close to the ask bar
       even on tall screens; it scrolls inside the cap */
    .tavern {
      flex: 0 1 auto;
      min-height: 0;
      max-height: 16cm;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      padding: 1.25rem;
      margin-bottom: 0.9rem;
      overflow-y: auto;
      overscroll-behavior: contain;
    }

    .bubble {
      max-width: 88%;
      padding: 0.75rem 1rem;
      border-radius: var(--radius);
      box-shadow: 0 2px 10px rgba(59, 47, 35, 0.08);
      animation: rise 0.25s ease-out;
    }

    .bubble-tender {
      align-self: flex-start;
      background: var(--card);
      border: 1px solid #e7dcc6;
      border-top-left-radius: 4px;
    }

    .bubble-user {
      align-self: flex-end;
      background: linear-gradient(160deg, #d9a45a, var(--amber));
      color: #fffdf7;
      border-top-right-radius: 4px;
    }

    .thinking {
      color: var(--ink-soft);
      font-style: italic;
    }

    .bubble-error {
      align-self: center;
      background: #fbeeea;
      border: 1px solid #e5b8ab;
      color: #7a3b28;
      font-size: 0.9rem;
    }

    @keyframes rise {
      from {
        transform: translateY(6px);
        opacity: 0.4;
      }
      to {
        transform: none;
        opacity: 1;
      }
    }

    /* the ask bar */
    .askbar {
      display: flex;
      gap: 0.5rem;
      background: var(--card);
      border: 1px solid #e7dcc6;
      border-radius: var(--radius);
      padding: 0.5rem;
      box-shadow: 0 4px 14px rgba(59, 47, 35, 0.1);
    }

    .askbar input {
      flex: 1;
      border: none;
      background: transparent;
      font: inherit;
      color: var(--ink);
      padding: 0.5rem 0.75rem;
      outline: none;
    }
    .askbar input::placeholder {
      color: var(--ink-soft);
      font-style: italic;
    }

    .askbar button {
      border: none;
      border-radius: 10px;
      background: var(--amber);
      color: #fffdf7;
      font: inherit;
      font-weight: 600;
      padding: 0.45rem 1.1rem;
      cursor: pointer;
      transition: background 0.15s ease;
    }
    .askbar button:hover:not(:disabled) {
      background: var(--amber-deep);
    }
    .askbar button:disabled {
      opacity: 0.55;
      cursor: default;
    }

    .notice {
      margin-top: 0.9rem;
      text-align: center;
      font-size: 0.78rem;
      color: var(--ink-soft);
    }
    .notice p {
      margin: 0.4rem 0;
    }

    @media (max-width: 480px) {
      .bubble {
        max-width: 94%;
      }
    }
  `;

  firstUpdated() {
    this._input = this.renderRoot.querySelector('input');
    this._input?.focus();
  }

  updated() {
    // keep the newest bubbles in view
    const tavern = this.renderRoot.querySelector('.tavern');
    if (tavern) tavern.scrollTop = tavern.scrollHeight;
  }

  send(event) {
    event.preventDefault();
    const question = this.draft.trim();
    if (!question || this.busy) return;
    this.lines = [...this.lines, { role: 'user', text: question }];
    this.draft = '';
    this._input.value = ''; // belt-and-braces: never leave typed text behind
    this.busy = true;
    this.error = null;
    this._ask(question)
      .then((answer) => {
        this.lines = [...this.lines, { role: 'assistant', text: answer }];
      })
      .catch((err) => {
        this.error = String(err?.message ?? err);
      })
      .finally(() => {
        this.busy = false;
        this._input?.focus();
      });
  }

  async _ask(question) {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => null);
      throw new Error(detail?.detail?.[0]?.msg ?? `HTTP ${res.status}`);
    }
    return (await res.json()).answer;
  }

  static REPLIES = [
    "Is there something more I can help you with?",
    "Still thirsty?",
    "There is no such thing as a hurry with a good beer",
    "Take your time — the next pint isn't going anywhere",
    "Another round, perhaps?",
    "The cellar is full; what else can I fetch you?",
    "A good pour deserves company — anything else?",
    "One suggestion down; what shall we try next?",
  ];

  get placeholder() {
    const served = this.lines.filter((l) => l.role === 'assistant').length;
    if (!served) return 'What would you like to drink?';
    return SommebeerChat.REPLIES[(served - 1) % SommebeerChat.REPLIES.length];
  }

  render() {
    return html`
      <main class="wrap">
        <header>
          <h1>sommebeer <span aria-hidden="true">🍺</span></h1>
          <p class="tagline">
            your beer store tender — questions or a beer you like, it makes a suggestion
          </p>
        </header>

        <section class="tavern" aria-live="polite">
          ${this.lines.length === 0 && !this.busy
            ? html`<div class="bubble bubble-tender">
                Tell me a style ("something strong and fruity") or a beer you like ("similar to
                Flower Power") and I'll bring a suggestion from the shelf.
              </div>`
            : nothing}
          ${this.lines.map(
            (m) =>
              html`<div
                class=${`bubble ${m.role === 'user' ? 'bubble-user' : 'bubble-tender'}`}
              >
                ${m.role === 'assistant'
                  ? html`<md-block text=${m.text}></md-block>`
                  : m.text}
              </div>`,
          )}
          ${this.busy
            ? html`<div class="bubble bubble-tender thinking">
                the tender is going down to the cellar…
              </div>`
            : nothing}
          ${this.error
            ? html`<div class="bubble bubble-error">⚠ ${this.error}</div>`
            : nothing}
        </section>

        <form class="askbar" @submit=${this.send}>
          <input
            value=${this.draft}
            maxlength="2000"
            placeholder=${this.placeholder}
            @input=${(e) => (this.draft = e.currentTarget.value)}
            ?disabled=${this.busy}
          />
          <button type="submit" ?disabled=${this.busy || !this.draft.trim()}>
            ${this.busy ? '…' : 'send'}
          </button>
        </form>

        <footer class="notice">
          <p>
            ⚠️ alcohol consumption is <strong>discouraged</strong>; for adults (18+). Drink
            responsibly.
          </p>
        </footer>
      </main>
    `;
  }
}

customElements.define('sommebeer-chat', SommebeerChat);
