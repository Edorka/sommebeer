import { LitElement, css, html, nothing } from 'lit';
import './md-block.js';

/**
 * sommebeer-chat — the conversation itself: transcript + ask bar.
 * Policy lives up the tree: `acknowledged` (agreement state) and
 * `agreementTitle` (hover hint) arrive one-way from sommebeer-t-c.
 */
export class SommebeerChat extends LitElement {
  static properties = {
    acknowledged: { type: Boolean },
    agreementTitle: { type: String, attribute: 'agreement-title' },
    lines: { state: true },
    draft: { state: true },
    busy: { state: true },
    error: { state: true },
  };

  constructor() {
    super();
    this.acknowledged = false;
    this.agreementTitle = '';
    this.lines = [];
    this.draft = '';
    this.busy = false;
    this.error = null;
  }

  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
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

    /* the thumbs row: subordinate, shows up only for real answers */
    .feedback {
      display: flex;
      gap: 0.25rem;
      justify-content: flex-end;
      margin-top: 0.5rem;
    }
    .feedback button {
      border: none;
      background: none;
      cursor: pointer;
      font-size: 0.95rem;
      opacity: 0.45;
      padding: 0.1rem 0.25rem;
      border-radius: 6px;
      transition: opacity 0.15s ease, transform 0.15s ease;
    }
    .feedback button:hover {
      opacity: 0.95;
      transform: scale(1.1);
    }
    .feedback button:disabled {
      cursor: default;
      opacity: 0.3;
    }
    .feedback button.voted {
      opacity: 1;
      background: var(--paper-deep);
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

    @media (max-width: 480px) {
      .bubble {
        max-width: 94%;
      }
    }
  `;

  static REPLIES = [
    'Is there something more I can help you with?',
    'Still thirsty?',
    'There is no such thing as a hurry with a good beer',
    "Take your time — the next pint isn't going anywhere",
    'Another round, perhaps?',
    'The cellar is full; what else can I fetch you?',
    'A good pour deserves company — anything else?',
    'One suggestion down; what shall we try next?',
  ];

  get placeholder() {
    const served = this.lines.filter((l) => l.role === 'assistant').length;
    if (!served) return 'What would you like to drink?';
    return SommebeerChat.REPLIES[(served - 1) % SommebeerChat.REPLIES.length];
  }

  firstUpdated() {
    this._input = this.renderRoot.querySelector('input');
    if (this.acknowledged) this._input?.focus();
  }

  updated() {
    // keep the newest bubbles in view
    const tavern = this.renderRoot.querySelector('.tavern');
    if (tavern) tavern.scrollTop = tavern.scrollHeight;
  }

  send(event) {
    event.preventDefault();
    if (!this.acknowledged || this.busy) return;
    const question = this.draft.trim();
    if (!question) return;
    this.lines = [...this.lines, { role: 'user', text: question }];
    this.draft = '';
    this._input.value = ''; // belt-and-braces: never leave typed text behind
    this.busy = true;
    this.error = null;
    this._ask(question)
      .then((response) => {
        this.lines = [
          ...this.lines,
          {
            role: 'assistant',
            text: response.answer,
            traceId: response.trace_id,
            spanId: response.span_id,
            rating: null,
          },
        ];
      })      .catch((err) => {
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
    return await res.json();
  }

  /**
   * Thumbs on one answer go straight into Phoenix as a span annotation.
   * Re-voting simply posts again: the backend keys the annotation to the
   * turn, so it replaces rather than stacks.
   */
  async vote(index, rating) {
    const message = this.lines[index];
    if (!message?.spanId || message.rating === rating) return;
    const previous = message.rating;
    try {
      this.lines = this.lines.map((m, i) =>
        i === index ? { ...m, rating } : m);
      const res = await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trace_id: message.traceId,
          span_id: message.spanId,
          rating,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
    } catch (err) {
      // restore the previous visual state; the UI never gainsays the server
      this.lines = this.lines.map((m, i) =>
        i === index ? { ...m, rating: previous } : m
      );
      this.error = typeof err === 'string' ? err : (err?.message ?? String(err));
    }
  }

  render() {
    const blocked = !this.acknowledged || this.busy;
    return html`
      <section class="tavern" aria-live="polite">
        ${this.lines.length === 0 && !this.busy
          ? html`<div class="bubble bubble-tender">
              Tell me a style ("something strong and fruity") or a beer you like ("similar to
              Flower Power") and I'll bring a suggestion from the shelf.
            </div>`
          : nothing}
        ${this.lines.map(
          (m, i) =>
            html`<div
              class=${`bubble ${m.role === 'user' ? 'bubble-user' : 'bubble-tender'}`}
            >
              ${m.role === 'assistant'
                ? html`<md-block text=${m.text}></md-block>`
                : m.text}
              ${m.role === 'assistant' && m.spanId
                ? html`<span class="feedback">
                    <button
                      type="button"
                      class=${m.rating === 'up' ? 'voted' : ''}
                      aria-label="good answer"
                      title="told the tender this was useful"
                      @click=${() => this.vote(i, 'up')}
                    >👍</button>
                    <button
                      type="button"
                      class=${m.rating === 'down' ? 'voted' : ''}
                      aria-label="bad answer"
                      title="told the tender this missed"
                      @click=${() => this.vote(i, 'down')}
                    >👎</button>
                  </span>`
                : nothing}
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
          ?disabled=${blocked}
          title=${this.acknowledged ? '' : this.agreementTitle}
        />
        <button
          type="submit"
          ?disabled=${blocked || !this.draft.trim()}
          title=${this.acknowledged ? '' : this.agreementTitle}
        >
          ${this.busy ? '…' : 'send'}
        </button>
      </form>
    `;
  }
}

customElements.define('sommebeer-chat', SommebeerChat);
