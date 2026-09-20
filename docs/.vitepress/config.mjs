import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  base: "/QuickView",
  title: "The QuickView Family",
  description:
    "How to use the QuickView family of tools to look at Earth system simulation data",
  head: [["link", { rel: "stylesheet", href: "custom.css" }]],
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    search: {
      provider: "local",
    },
    logo: "/icon-full.png",
    nav: [
      { text: "Home", link: "/" },
      { text: "News", link: "/webnews" },
      { text: "Gallery", link: "/gallery/" },
      { text: "User's Guide", link: "/guides/reminders" },
      { text: "At NERSC", link: "/nersc/launching" },
    ],

    sidebar: {
      "/nersc/": [
        {
          text: "Installation at NERSC",
          items: [
            { text: "Public installation",  link: "/nersc/installation_public" },
            { text: "Personal installation",link: "/nersc/installation_personal" },
            { text: "E3SM-Unified",         link: "/nersc/installation_E3SM-unified" },
         ],
        },
        {
          text: "Launching at NERSC",
          items: [
            { text: "Overview",   link: "/nersc/launching" },
            { text: "VS Code",    link: "/nersc/login_vscode" },
            { text: "JupyterHub", link: "/nersc/login_jupyter" },
          ],
        },
      ],
      "/guides/": [
        {
          text: "Introduction",
          items: [
            { text: "Overview", link: "/guides/reminders" },
            { text: "Connecitiviy Files", link: "/guides/connectivity" },
            { text: "Simulation Files", link: "/guides/simulation_data" },
            { text: "Install and Launch", link: "/guides/install_and_launch" },
          ],
        },
        {
          text: "QuickView User's Guide",
          collapsed: true,
          items: [
            { text: "What is QuickView?", link: "/guides/quickview/index" },
            { text: "Getting Started",    link: "/guides/quickview/getting_started" },
            { text: "UI Overview",        link: "/guides/quickview/ui_overview" },
            { text: "Keyboard Shortcuts", link: "/guides/quickview/shortcuts" },
            { text: "File Selection",     link: "/guides/quickview/file_selection", },
            { text: "Variable Selection", link: "/guides/quickview/variable_selection", },
            { text: "Slice Selection",    link: "/guides/quickview/slice_selection", },
            { text: "Viewport Layout",    link: "/guides/quickview/viewport_layout", },
            { text: "Individual Views",   link: "/guides/quickview/individual_views", },
            { text: "Map-related Features", link: "/guides/quickview/map_projections" },
            { text: "Cursor Probe",       link: "/guides/quickview/cursor_probe" },
            { text: "Saving Images",      link: "/guides/quickview/saving_images" },
          ],
        },
        {
          text: "QuickCompare User's Guide",
          collapsed: true,
          items: [
            { text: "What is QuickCompare?", link: "/guides/quickcompare/index", },
            { text: "Getting Started",       link: "/guides/quickcompare/getting_started" },
            { text: "UI Overview",           link: "/guides/quickcompare/ui_overview_and_shortcuts" },
            { text: "File Selection",        link: "/guides/quickcompare/file_selection", },
            { text: "Variables and Slices",  link: "/guides/quickcompare/variable_and_slice_selection", },
            { text: "Two-sim. Comparison",   link: "/guides/quickcompare/two-sim_comparison", },
            { text: "Multi-sim. Comparison", link: "/guides/quickcompare/multi-sim_comparison", },
            { text: "Miscellaneous",         link: "/guides/quickcompare/miscellaneous" },
          ],
        },
        {
          text: "Tools In Development",
          items: [{ text: "SiteView" }, { text: "CondiDiag Viewer" }],
        },
        {
          text: "For App Developers",
          items: [
            { text: "Setup", link: "/guides/dev/setup" },
            { text: "Continuous Integration", link: "/guides/dev/ci" },
          ],
        },
      ],
    },

    socialLinks: [
      { icon: "github", link: "https://github.com/Kitware/QuickView" },
    ],
  },

  markdown: {
    // Options for the Table of Contents plugin
    toc: {
      level: [2, 3], // Only include <h2> and <h3> in the TOC
    },
    // Options for heading anchors (optional)
    anchor: {
      permalink: true, // Enables clickable anchor links on headings
    },
  },
});
