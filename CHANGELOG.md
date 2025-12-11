# Changelog

## [0.3.0](https://github.com/loonghao/auroraview-dcc-shelves/compare/v0.2.0...v0.3.0) (2025-12-11)


### Features

* add bottom panel with detail and console tabs ([aaef647](https://github.com/loonghao/auroraview-dcc-shelves/commit/aaef647a1f179281ab5be9f9cf9e0f2127b96219))
* add DCC adapter system and host-based tool filtering ([d499724](https://github.com/loonghao/auroraview-dcc-shelves/commit/d4997244ba8a488f8a634c37b419dfcab03931d2))
* add desktop mode, zoom support, and comprehensive UI tests ([ea1b323](https://github.com/loonghao/auroraview-dcc-shelves/commit/ea1b3237e8382761d5e715cd73b31a6aac3da1cc))
* add settings panel with search paths and environment variables ([d371daa](https://github.com/loonghao/auroraview-dcc-shelves/commit/d371daa975551addb41410c3aaa55c21fbe392b8))
* add support for opening settings in a new window ([ca6cfcf](https://github.com/loonghao/auroraview-dcc-shelves/commit/ca6cfcf68e85c27c3fcda17636406ae50c9f715d))
* add Vite plugin for child window HTML path fix and unify window size config ([a14548d](https://github.com/loonghao/auroraview-dcc-shelves/commit/a14548d60b4119f8092fdae97e9b6a3655f40637))
* **api:** add Loading State, Zoom, and Warmup APIs to ShelfApp ([243f9d0](https://github.com/loonghao/auroraview-dcc-shelves/commit/243f9d0d1608d21312069cb4258eafc3d527835d))
* improve detail panel and add local icon support ([87d5a5e](https://github.com/loonghao/auroraview-dcc-shelves/commit/87d5a5ebb9a38faa391a60d3bf64a70e71c9f1bb))
* **qt:** add use_native_window option for native Qt window appearance ([44f035e](https://github.com/loonghao/auroraview-dcc-shelves/commit/44f035eed83601c2945ad2c26a4afb771c8356ec))


### Bug Fixes

* add lib modules to git and update gitignore ([135a8b4](https://github.com/loonghao/auroraview-dcc-shelves/commit/135a8b491cc3f80b34f156a5b98833c5f4b5059f))
* add missing lib modules and update version to 0.2.0 ([daa8d19](https://github.com/loonghao/auroraview-dcc-shelves/commit/daa8d19532d13214af246b514b64f410d334c3b9))
* apply pre-commit fixes and remove npm-lint hook ([b1643ea](https://github.com/loonghao/auroraview-dcc-shelves/commit/b1643eaa56d796719461da3acdeaa7707ba1534b))
* apply Qt6 dialog optimizations using unified function ([d13fa99](https://github.com/loonghao/auroraview-dcc-shelves/commit/d13fa99f4c75adf39e20a3647f31ba5c9c16e4a0))
* auto-fallback to modal in DCC WebView environments ([a47561d](https://github.com/loonghao/auroraview-dcc-shelves/commit/a47561d7db09ad7fc56848fd75b0285327a31606))
* prevent duplicate API registration causing Maya UI freeze ([64bd932](https://github.com/loonghao/auroraview-dcc-shelves/commit/64bd932f569c916c5e4c14eddaa6f06edcab6ede))
* resolve icon paths relative to config file location ([d2800fb](https://github.com/loonghao/auroraview-dcc-shelves/commit/d2800fb46e9cd5d2a9d34162015c257be7472fe2))
* **tests:** update tests for auroraview 0.3.10 API changes ([23b6185](https://github.com/loonghao/auroraview-dcc-shelves/commit/23b6185d46804eace722526f6249ea1d2d381e44))


### Performance Improvements

* optimize geometry fix and API registration ([7c0d5f0](https://github.com/loonghao/auroraview-dcc-shelves/commit/7c0d5f0824f1d97e4078e398193a9da72ef1fe2f))


### Documentation

* add Qt5/Qt6 compatibility guide ([602562e](https://github.com/loonghao/auroraview-dcc-shelves/commit/602562e004cd554a494d5774f141ec58893fe11e))
* add Qt6 optimization fix summary ([d8d4c87](https://github.com/loonghao/auroraview-dcc-shelves/commit/d8d4c875b415f0f2e288671618a92cfc8bed072d))

## [0.2.0](https://github.com/loonghao/auroraview-dcc-shelves/compare/v0.1.0...v0.2.0) (2025-12-01)


### Features

* add i18n internationalization support with Chinese translations ([d82fc98](https://github.com/loonghao/auroraview-dcc-shelves/commit/d82fc98f896924b160850714a8500fc6a7c41676))
* add startup optimization and window size persistence ([0513c2f](https://github.com/loonghao/auroraview-dcc-shelves/commit/0513c2fb0c62d49867ba46e4b8228af801da9439))
* migrate frontend from Vue to React ([dde80a8](https://github.com/loonghao/auroraview-dcc-shelves/commit/dde80a8f0d547489fa8e292675c71826bf9fb8bd))


### Bug Fixes

* add package-lock.json and Linux system dependencies for CI ([81d6dd1](https://github.com/loonghao/auroraview-dcc-shelves/commit/81d6dd13a30dffc83e1df4e00e91995b64691381))
* correct CI dependencies and uv sync command ([87b500e](https://github.com/loonghao/auroraview-dcc-shelves/commit/87b500e50ed94edd22e40c855b6b1703e061ac1d))
* downgrade dependencies to match lightbox-shelves versions ([c72a1cc](https://github.com/loonghao/auroraview-dcc-shelves/commit/c72a1ccd399106fe765e13f38bc0125a4ca2272f))
* improve tab button styling with inline styles ([dbbbca5](https://github.com/loonghao/auroraview-dcc-shelves/commit/dbbbca58fa08fecb148332792f3b622ddfdb51aa))
* resolve all ruff lint errors and exclude examples from checks ([310f42c](https://github.com/loonghao/auroraview-dcc-shelves/commit/310f42cd996aa1b61f844547c6151425932d7c4b))
* resolve ruff lint errors and add pre-commit configuration ([e363b1d](https://github.com/loonghao/auroraview-dcc-shelves/commit/e363b1d67eb662326139e653307a35fc2e6a8c55))
