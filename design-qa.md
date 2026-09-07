**Comparison target**

- Source visual truth: `C:\Users\29580\AppData\Local\Temp\codex-clipboard-3c64a743-0283-4378-b287-0fe3dc2882b0.png`
- Rendered implementation: `D:\Agent\FPZS\tmp\order-inspector-final.png`
- Full-view comparison: `D:\Agent\FPZS\tmp\design-qa-comparison.png`
- Focused inspector comparison: `D:\Agent\FPZS\tmp\design-qa-focused-comparison.png`
- Source pixels: 1672 × 941. Implementation pixels: 365 × 898.
- Implementation viewport: 365 × 898 CSS px in the Codex in-app browser; screenshot density treated as 1× because capture pixels match the browser viewport.
- State: an order row is selected and its detail inspector is open; the record has linked invoices, an outstanding balance, and a review warning.
- Normalization: the full source was proportionally scaled to 720 px high for the full-view composite. For the focused comparison, the source inspector region was cropped without distortion and proportionally scaled to 898 px high beside the implementation capture.
- The source is a directional desktop reference rather than a pixel-perfect product spec. The implementation keeps the existing product's typography, tokens, data fields, and editing routes.

**Findings**

- No actionable P0, P1, or P2 findings remain for the selected right-side detail pattern.
- Fonts and typography: the implementation retains the product's Microsoft YaHei/PingFang/system stack, uses a clear type hierarchy, and keeps amounts tabular and visually prominent. The narrower verification viewport creates more wrapping than the reference, but the content remains readable.
- Spacing and layout rhythm: sections, separators, two-column definition grids, and a fixed action footer reproduce the reference's scan order. The desktop inspector width is now responsive from 420 to 560 px; viewports at or below 900 px switch to a full-screen inspector.
- Colors and visual tokens: blue actions, green paid values, red outstanding values, neutral dividers, and white surfaces use the existing design tokens and match the reference's semantic hierarchy.
- Image and asset fidelity: neither the selected detail surface nor the implementation requires photographic or branded image assets. No placeholder imagery, emoji, or custom-drawn icon substitutes were introduced.
- Copy and content: invoice and order inspectors use business-specific labels and expose basic data, amounts, payment state, related documents, review information, source file, and timestamps. Existing edit routes and confirmation wording are preserved.

**Full-view comparison evidence**

- The source establishes a master-detail composition with the list retained on the left and a persistent inspector on the right.
- The implementation follows that composition on desktop and deliberately changes to a full-screen inspector at narrow widths so background controls do not leak into or compete with the detail task.

**Focused region comparison evidence**

- The focused comparison confirms the same core hierarchy: record identity, basic information, financial state, document relationships, review information, and persistent edit/confirm actions.
- Timeline history and an inline note editor shown in the reference are not present because the current application has no corresponding audit-history or note-editing data model. This is classified as future functionality, not visual drift in the requested detail display.

**Comparison history**

- Iteration 1 — P2: at a 365 px viewport, the desktop docked inspector left a narrow strip of underlying page controls visible. Fix: made the inspector width viewport-aware and added a full-screen inspector mode at 900 px and below.
- Iteration 2 — P2: the mobile full-screen mode still reserved the desktop 64 px top offset, exposing underlying header actions. Fix: changed the narrow-layout inspector inset to `0` on all sides.
- Iteration 3 — passed: the revised capture `D:\Agent\FPZS\tmp\order-inspector-final.png` shows a clean, uninterrupted inspector, readable two-column data, independently scrollable content, and persistent actions.

**Primary interactions tested**

- Open order details by clicking a table row.
- Close the inspector and return focus to the selected row.
- Open invoice details by clicking a table row.
- Confirm an invoice in a copied test database and verify the status/button updates to 已确认.
- Invoice and order inline scripts passed syntax checks; Python modules compiled successfully.

**Implementation checklist**

- [x] Clickable and keyboard-focusable ledger rows.
- [x] Right-side desktop inspector and full-screen narrow-layout fallback.
- [x] Invoice and order business-detail sections.
- [x] Existing edit routes exposed from the inspector.
- [x] Confirm action with loading, success, and error feedback.
- [x] Close button, Escape handling, selected-row state, and focus return.

**Follow-up polish**

- P3: make related invoice/order numbers navigate directly to their corresponding detail record after cross-ledger lookup is added.
- P3: add editable notes and an audit timeline when those fields exist in the backend.

final result: passed
