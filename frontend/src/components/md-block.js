import { LitElement, css } from 'lit';
import { html } from 'lit';
import { renderMarkdown } from '../markdown.js';

/**
 * The tender's reply, rendered as Markdown inside a shadow root.
 * Styling stays local to this component.
 */
export class MdBlock extends LitElement {
  static properties = { text: { type: String } };

  static styles = css`
    :host {
      display: block;
    }
    :is(p, ul, ol, li) {
      margin: 0.3rem 0;
    }
    :is(h1, h2, h3) {
      margin: 0.6rem 0 0.3rem;
      color: var(--amber-deep);
      font-size: 1.05rem;
    }
    strong {
      color: var(--amber);
    }
    code {
      background: var(--paper-deep);
      padding: 0.1em 0.35em;
      border-radius: 6px;
      font-size: 0.85em;
    }
    ul,
    ol {
      padding-left: 1.25rem;
    }
    /* links inherit the bubble's colour instead of user-agent blue */
    a {
      color: inherit;
      text-decoration-color: var(--amber);
    }
  `;

  render() {
    return renderMarkdown(this.text ?? '');
  }
}

customElements.define('md-block', MdBlock);
