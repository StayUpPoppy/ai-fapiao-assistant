(() => {
  const page = document.body.dataset.page;

  if (!page || page === "login") {
    return;
  }

  const pageConfig = {
    dashboard: { crumb: "工作台", title: "工作台" },
    invoices: { crumb: "发票台账", title: "发票台账" },
    entry: { crumb: "智能录入", title: "智能录入发票" },
    orders: { crumb: "订单台账", title: "订单台账" },
    invoiceEdit: { crumb: "发票台账", title: "更新发票台账" },
    orderEdit: { crumb: "订单台账", title: "更新订单台账" }
  };

  const config = pageConfig[page] || pageConfig.dashboard;
  const activeSection = ["orders", "orderEdit"].includes(page)
    ? "orders"
    : page === "entry"
      ? "entry"
      : ["invoices", "invoiceEdit"].includes(page)
        ? "invoices"
        : "dashboard";

  const navItems = [
    {
      key: "dashboard",
      label: "工作台",
      href: "/",
      icon: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V10Z"/><path d="M9 21v-6h6v6"/></svg>'
    },
    {
      key: "invoices",
      label: "发票台账",
      href: "/static/invoices.html",
      icon: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h4M9 11h6M9 15h6M9 19h4"/></svg>'
    },
    {
      key: "orders",
      label: "订单台账",
      href: "/static/orders.html",
      icon: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v14H4z"/><path d="M4 10h16M8 5v14M14 10v9"/></svg>'
    }
  ];

  const main = document.querySelector("main.page");

  if (!main) {
    return;
  }

  const sidebar = document.createElement("aside");
  sidebar.className = "app-sidebar";
  sidebar.innerHTML = `
    <a class="app-brand" href="/" aria-label="返回工作台">
      <span class="app-brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 3h9l5 5v13H5z"/><path d="M14 3v5h5M8 14h8M8 18h5"/></svg></span>
      <span>供应链台账助手</span>
    </a>
    <nav class="app-nav" aria-label="主导航">
      ${navItems.map((item) => `
        <a class="app-nav-link ${activeSection === item.key ? "is-active" : ""}" href="${item.href}">
          <span class="app-nav-icon" aria-hidden="true">${item.icon}</span>
          <span>${item.label}</span>
        </a>
      `).join("")}
    </nav>
    <div class="sidebar-bottom">
      <a class="quick-entry" href="/api/export/ledger.xlsx">
        <span class="app-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></svg></span>
        <span>导出 Excel</span>
      </a>
    </div>
  `;

  const topbar = document.createElement("header");
  topbar.className = "app-topbar";
  topbar.innerHTML = `
    <div class="app-breadcrumb"><span>供应链台账助手</span><span class="breadcrumb-separator">/</span><strong>${config.crumb}</strong></div>
    <div class="topbar-meta"><span class="presence-dot" aria-hidden="true"></span><span>业务工作台</span></div>
  `;

  const stage = document.createElement("div");
  stage.className = "app-stage";
  const shell = document.createElement("div");
  shell.className = "app-shell";

  main.parentNode.insertBefore(shell, main);
  shell.append(sidebar, stage);
  stage.append(topbar, main);
  document.body.classList.add("app-page");
  document.title = `${config.title}｜供应链台账助手`;
})();

window.LedgerUI = window.LedgerUI || {};

const PDFJS_ASSET_BASE = "/static/vendor/pdfjs";
const PDFJS_VERSION = "6.3.289";
let pdfJsModulePromise = null;

function loadPdfJsModule() {
  if (!pdfJsModulePromise) {
    pdfJsModulePromise = import(
      `${PDFJS_ASSET_BASE}/pdf.min.mjs?v=${PDFJS_VERSION}`
    ).then((pdfjs) => {
      pdfjs.GlobalWorkerOptions.workerSrc =
        `${PDFJS_ASSET_BASE}/pdf.worker.min.mjs?v=${PDFJS_VERSION}`;
      return pdfjs;
    });
  }
  return pdfJsModulePromise;
}

window.LedgerUI.createLocalFilePreview = ({
  inputId,
  emptyId,
  contentId,
  imageHostId,
  pdfId,
  filenameId,
  metaId,
  openButtonId
}) => {
  const input = document.getElementById(inputId);
  const empty = document.getElementById(emptyId);
  const content = document.getElementById(contentId);
  const imageHost = document.getElementById(imageHostId);
  const pdf = document.getElementById(pdfId);
  const filename = document.getElementById(filenameId);
  const meta = document.getElementById(metaId);
  const openButton = document.getElementById(openButtonId);
  const toolbar = openButton.closest(".source-preview-toolbar");
  const previewActions = document.createElement("div");
  const zoomControls = document.createElement("div");
  const zoomOutButton = document.createElement("button");
  const zoomResetButton = document.createElement("button");
  const zoomInButton = document.createElement("button");
  let objectUrl = null;
  let dragState = null;
  let renderVersion = 0;
  let pdfLoadingTask = null;
  let previewKind = null;
  let previewZoom = 1;
  let activeImage = null;

  const MIN_PREVIEW_ZOOM = 0.5;
  const MAX_PREVIEW_ZOOM = 2.5;
  const PREVIEW_ZOOM_STEP = 0.25;

  previewActions.className = "source-preview-actions";
  zoomControls.className = "source-preview-zoom";
  zoomControls.setAttribute("role", "group");
  zoomControls.setAttribute("aria-label", "源文件缩放");
  zoomControls.hidden = true;

  zoomOutButton.className = "source-preview-zoom-button";
  zoomOutButton.type = "button";
  zoomOutButton.title = "缩小预览";
  zoomOutButton.setAttribute("aria-label", "缩小预览");
  zoomOutButton.innerHTML =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 12h12"/></svg>';

  zoomResetButton.className = "source-preview-zoom-reset";
  zoomResetButton.type = "button";
  zoomResetButton.title = "恢复适合宽度";
  zoomResetButton.setAttribute("aria-label", "恢复适合宽度，当前 100%");
  zoomResetButton.textContent = "100%";

  zoomInButton.className = "source-preview-zoom-button";
  zoomInButton.type = "button";
  zoomInButton.title = "放大预览";
  zoomInButton.setAttribute("aria-label", "放大预览");
  zoomInButton.innerHTML =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 6v12M6 12h12"/></svg>';

  zoomControls.append(zoomOutButton, zoomResetButton, zoomInButton);
  toolbar.insertBefore(previewActions, openButton);
  previewActions.append(zoomControls, openButton);

  function getActivePreviewHost() {
    if (previewKind === "pdf") return pdf;
    if (previewKind === "image") return imageHost;
    return null;
  }

  function updateZoomControls() {
    const percentage = Math.round(previewZoom * 100);
    zoomResetButton.textContent = `${percentage}%`;
    zoomResetButton.setAttribute(
      "aria-label",
      `恢复适合宽度，当前 ${percentage}%`
    );
    zoomOutButton.disabled = previewZoom <= MIN_PREVIEW_ZOOM;
    zoomInButton.disabled = previewZoom >= MAX_PREVIEW_ZOOM;
  }

  function applyPreviewZoom(nextZoom, anchor = {}) {
    const host = getActivePreviewHost();
    if (!host) return;

    const boundedZoom = Math.min(
      MAX_PREVIEW_ZOOM,
      Math.max(MIN_PREVIEW_ZOOM, nextZoom)
    );
    if (boundedZoom === previewZoom) return;

    const anchorX = anchor.x ?? host.clientWidth / 2;
    const anchorY = anchor.y ?? host.clientHeight / 2;
    const contentXRatio = (host.scrollLeft + anchorX) / Math.max(host.scrollWidth, 1);
    const contentYRatio = (host.scrollTop + anchorY) / Math.max(host.scrollHeight, 1);
    previewZoom = boundedZoom;

    if (previewKind === "image" && activeImage) {
      activeImage.style.width = `${previewZoom * 100}%`;
    } else if (previewKind === "pdf") {
      pdf.querySelectorAll("canvas[data-preview-width]").forEach((canvas) => {
        const width = Number(canvas.dataset.previewWidth);
        const height = Number(canvas.dataset.previewHeight);
        canvas.style.width = `${Math.round(width * previewZoom)}px`;
        canvas.style.height = `${Math.round(height * previewZoom)}px`;
      });
    }

    updateZoomControls();
    requestAnimationFrame(() => {
      host.scrollLeft = contentXRatio * host.scrollWidth - anchorX;
      host.scrollTop = contentYRatio * host.scrollHeight - anchorY;
    });
  }

  function handlePreviewZoomWheel(host, event) {
    if (!event.ctrlKey || host !== getActivePreviewHost()) return;
    event.preventDefault();
    const bounds = host.getBoundingClientRect();
    const direction = event.deltaY < 0 ? 1 : -1;
    applyPreviewZoom(
      previewZoom + direction * PREVIEW_ZOOM_STEP,
      { x: event.clientX - bounds.left, y: event.clientY - bounds.top }
    );
  }

  function stopGrabScroll(event) {
    if (!dragState || (event && event.pointerId !== dragState.pointerId)) return;
    const { host, pointerId } = dragState;
    dragState = null;
    host.classList.remove("is-dragging");
    if (host.hasPointerCapture?.(pointerId)) {
      host.releasePointerCapture(pointerId);
    }
  }

  function startGrabScroll(host, event) {
    // Touch devices keep their native one-finger scrolling and pinch gestures.
    if (event.pointerType === "touch" || event.button !== 0) return;
    const canScroll =
      host.scrollHeight > host.clientHeight || host.scrollWidth > host.clientWidth;
    if (!canScroll) return;
    dragState = {
      host,
      pointerId: event.pointerId,
      clientX: event.clientX,
      clientY: event.clientY,
      scrollLeft: host.scrollLeft,
      scrollTop: host.scrollTop
    };
    host.classList.add("is-dragging");
    host.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  }

  function moveGrabScroll(host, event) {
    if (
      !dragState ||
      dragState.host !== host ||
      event.pointerId !== dragState.pointerId
    ) return;
    host.scrollLeft = dragState.scrollLeft - (event.clientX - dragState.clientX);
    host.scrollTop = dragState.scrollTop - (event.clientY - dragState.clientY);
    event.preventDefault();
  }

  function handlePreviewKeydown(host, event) {
    const pageDistance = Math.max(host.clientHeight * 0.82, 160);
    const distances = {
      ArrowUp: -56,
      ArrowDown: 56,
      PageUp: -pageDistance,
      PageDown: pageDistance
    };

    if (event.key === "Home") {
      host.scrollTop = 0;
    } else if (event.key === "End") {
      host.scrollTop = host.scrollHeight;
    } else if (Object.hasOwn(distances, event.key)) {
      host.scrollBy({ top: distances[event.key], behavior: "smooth" });
    } else {
      return;
    }
    event.preventDefault();
  }

  function bindGrabScroll(host) {
    host.addEventListener("pointerdown", (event) => startGrabScroll(host, event));
    host.addEventListener("pointermove", (event) => moveGrabScroll(host, event));
    host.addEventListener("pointerup", stopGrabScroll);
    host.addEventListener("pointercancel", stopGrabScroll);
    host.addEventListener("lostpointercapture", stopGrabScroll);
    host.addEventListener("keydown", (event) => handlePreviewKeydown(host, event));
    host.addEventListener(
      "wheel",
      (event) => handlePreviewZoomWheel(host, event),
      { passive: false }
    );
  }

  function releaseObjectUrl() {
    if (!objectUrl) return;
    URL.revokeObjectURL(objectUrl);
    objectUrl = null;
  }

  function formatFileSize(size) {
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

  function cancelPdfRendering() {
    renderVersion += 1;
    if (pdfLoadingTask) {
      const taskToDestroy = pdfLoadingTask;
      pdfLoadingTask = null;
      try {
        Promise.resolve(taskToDestroy.destroy()).catch(() => {});
      } catch (_error) {
        // A task that already finished cleanup does not need further action.
      }
    }
    pdf.replaceChildren();
    pdf.classList.remove("has-error");
    pdf.removeAttribute("aria-busy");
    pdf.scrollLeft = 0;
    pdf.scrollTop = 0;
  }

  function clear() {
    stopGrabScroll();
    cancelPdfRendering();
    releaseObjectUrl();
    imageHost.replaceChildren();
    imageHost.scrollLeft = 0;
    imageHost.scrollTop = 0;
    imageHost.hidden = true;
    pdf.hidden = true;
    previewKind = null;
    previewZoom = 1;
    activeImage = null;
    zoomControls.hidden = true;
    updateZoomControls();
    filename.textContent = "";
    meta.textContent = "";
    openButton.disabled = true;
    content.hidden = true;
    empty.hidden = false;
  }

  function createPreviewMessage(className, message) {
    const element = document.createElement("div");
    element.className = className;
    element.setAttribute("role", className.includes("error") ? "alert" : "status");
    element.textContent = message;
    return element;
  }

  async function renderPdf(file, version) {
    pdf.hidden = false;
    pdf.setAttribute("aria-busy", "true");
    pdf.append(createPreviewMessage("source-preview-loading", "正在生成 PDF 预览…"));

    try {
      const [pdfjs, fileBuffer] = await Promise.all([
        loadPdfJsModule(),
        file.arrayBuffer()
      ]);
      if (version !== renderVersion) return;

      pdfLoadingTask = pdfjs.getDocument({
        data: new Uint8Array(fileBuffer),
        cMapUrl: `${PDFJS_ASSET_BASE}/cmaps/`,
        cMapPacked: true,
        standardFontDataUrl: `${PDFJS_ASSET_BASE}/standard_fonts/`,
        wasmUrl: `${PDFJS_ASSET_BASE}/wasm/`
      });
      const pdfDocument = await pdfLoadingTask.promise;
      if (version !== renderVersion) return;

      const totalPages = pdfDocument.numPages;
      const previewPageLimit = Math.min(totalPages, 30);
      const availableWidth = Math.max(pdf.clientWidth - 28, 280);
      pdf.replaceChildren();

      for (let pageNumber = 1; pageNumber <= previewPageLimit; pageNumber += 1) {
        if (version !== renderVersion) return;
        const page = await pdfDocument.getPage(pageNumber);
        const originalViewport = page.getViewport({ scale: 1 });
        const viewport = page.getViewport({
          scale: availableWidth / originalViewport.width
        });
        const outputScale = Math.min(window.devicePixelRatio || 1, 2);
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d", { alpha: false });
        const pageCard = document.createElement("section");
        const pageLabel = document.createElement("div");

        pageCard.className = "source-preview-pdf-page";
        pageCard.setAttribute("aria-label", `PDF 第 ${pageNumber} 页`);
        pageLabel.className = "source-preview-page-label";
        pageLabel.textContent = `${pageNumber} / ${totalPages}`;
        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);
        canvas.dataset.previewWidth = `${viewport.width}`;
        canvas.dataset.previewHeight = `${viewport.height}`;
        canvas.style.width = `${Math.floor(viewport.width * previewZoom)}px`;
        canvas.style.height = `${Math.floor(viewport.height * previewZoom)}px`;
        canvas.setAttribute("role", "img");
        canvas.setAttribute("aria-label", `PDF 第 ${pageNumber} 页内容`);
        pageCard.append(pageLabel, canvas);
        pdf.append(pageCard);

        await page.render({
          canvasContext: context,
          viewport,
          transform: outputScale === 1
            ? null
            : [outputScale, 0, 0, outputScale, 0, 0]
        }).promise;
        page.cleanup();
        meta.textContent =
          `PDF · ${formatFileSize(file.size)} · ${pageNumber}/${totalPages} 页载入`;
      }

      if (totalPages > previewPageLimit) {
        pdf.append(createPreviewMessage(
          "source-preview-notice",
          `文件共 ${totalPages} 页，当前预览前 ${previewPageLimit} 页；可在新窗口查看全部。`
        ));
      }
      pdf.removeAttribute("aria-busy");
      meta.textContent =
        `PDF · ${formatFileSize(file.size)} · ${totalPages} 页 · 拖动浏览 · Ctrl+滚轮缩放`;
    } catch (error) {
      if (version !== renderVersion) return;
      console.error("PDF preview failed", error);
      pdf.replaceChildren(createPreviewMessage(
        "source-preview-error",
        "PDF 预览加载失败，请点击“新窗口打开”查看源文件。"
      ));
      pdf.classList.add("has-error");
      pdf.removeAttribute("aria-busy");
      meta.textContent = `PDF · ${formatFileSize(file.size)} · 预览加载失败`;
    }
  }

  function showFile(file) {
    clear();
    if (!file) return;

    const normalizedName = file.name.toLowerCase();
    const isPdf = file.type === "application/pdf" || normalizedName.endsWith(".pdf");
    const isImage = file.type.startsWith("image/") || /\.(png|jpe?g|webp)$/.test(normalizedName);
    if (!isPdf && !isImage) return;

    objectUrl = URL.createObjectURL(file);
    previewKind = isPdf ? "pdf" : "image";
    previewZoom = 1;
    zoomControls.hidden = false;
    updateZoomControls();
    filename.textContent = file.name;
    meta.textContent = isPdf
      ? `PDF · ${formatFileSize(file.size)} · 正在载入预览`
      : `图片 · ${formatFileSize(file.size)} · 拖动浏览 · Ctrl+滚轮缩放`;
    empty.hidden = true;
    content.hidden = false;
    openButton.disabled = false;

    if (isPdf) {
      void renderPdf(file, renderVersion);
    } else {
      const image = new Image();
      image.src = objectUrl;
      image.alt = `${file.name} 源文件预览`;
      image.draggable = false;
      activeImage = image;
      imageHost.append(image);
      imageHost.hidden = false;
    }
  }

  imageHost.tabIndex = 0;
  imageHost.setAttribute("role", "region");
  imageHost.setAttribute("aria-label", "图片源文件预览");
  bindGrabScroll(imageHost);
  bindGrabScroll(pdf);
  zoomOutButton.addEventListener("click", () => {
    applyPreviewZoom(previewZoom - PREVIEW_ZOOM_STEP);
  });
  zoomResetButton.addEventListener("click", () => applyPreviewZoom(1));
  zoomInButton.addEventListener("click", () => {
    applyPreviewZoom(previewZoom + PREVIEW_ZOOM_STEP);
  });
  input.addEventListener("change", () => showFile(input.files[0]));
  openButton.addEventListener("click", () => {
    if (objectUrl) window.open(objectUrl, "_blank", "noopener,noreferrer");
  });
  window.addEventListener("pagehide", releaseObjectUrl, { once: true });

  return { clear, showFile };
};
