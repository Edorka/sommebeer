import { LitElement, css, html } from 'lit';
import './sommebeer-chat.js';

/**
 * sommebeer-t-c — Terms & Conditions. Owns the agreement state: renders the
 * disclaimers and the "I understood" checkbox, and pushes the acknowledgment
 * down into the chat (one-way flow). Per-session confirmation: no persistence.
 */
export class SommebeerTc extends LitElement {
  static properties = {
    acknowledged: { state: true },
  };

  static AGREEMENT_TITLE =
    'You must confirm you understood the disclaimers above before asking the tender.';

  constructor() {
    super();
    this.acknowledged = false;
  }

  static styles = css`
    :host {
      /* grow to fill the wrap; lets the chat area keep its own scroll logic */
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
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
    .agree {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      margin: 0.4rem 0 0.6rem;
      cursor: pointer;
      color: var(--ink);
      font-size: 0.9rem;
    }
    .agree input {
      accent-color: var(--amber);
      cursor: pointer;
    }
  `;

  _toggle() {
    this.acknowledged = !this.acknowledged;
  }

  render() {
    return html`
      <sommebeer-chat
        .acknowledged=${this.acknowledged}
        .agreementTitle=${SommebeerTc.AGREEMENT_TITLE}
      ></sommebeer-chat>

      <footer class="notice">
        <p>
          ⚠️ alcohol consumption is <strong>discouraged</strong>; for adults (18+). Drink
          responsibly.
        </p>
        <p>🍜 conversations are saved for evaluation and product improvement.</p>
        <label class="agree">
          <input
            type="checkbox"
            ?checked=${this.acknowledged}
            @change=${this._toggle}
          />
          I understood
        </label>
      </footer>
    `;
  }
}

customElements.define('sommebeer-t-c', SommebeerTc);
