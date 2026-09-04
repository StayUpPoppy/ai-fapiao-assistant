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
