import { LitElement, css, html } from 'lit';
import './sommebeer-t-c.js';

/**
 * sommebeer-app — page shell: layout, palette tokens and the header.
 * Everything below it lives in sommebeer-t-c (agreement + footer) and
 * sommebeer-chat (the conversation itself).
 */
export class SommebeerApp extends LitElement {
  static styles = css`
    :host {
      /* palette — inherited by the child components' shadow roots */
      --paper: #f7f0e3;
      --paper-deep: #efe4d0;
      --ink: #3b2f23;
      --ink-soft: #7a6a55;
      --amber: #b3772f;
      --amber-deep: #8b5a1f;
      --card: #fffdf7;
      --radius: 14px;

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
  `;

  render() {
    return html`
      <main class="wrap">
        <header>
          <h1>sommebeer <span aria-hidden="true">🍺</span></h1>
          <p class="tagline">
            your beer store tender — questions or a beer you like, it makes a suggestion
          </p>
        </header>
        <sommebeer-t-c></sommebeer-t-c>
      </main>
    `;
  }
}

customElements.define('sommebeer-app', SommebeerApp);
