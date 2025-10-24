# CHANGELOG

<!-- version list -->

## v1.1.0 (2025-10-24)

### Bug Fixes

- Tauri save state and key binding
  ([`eb030a3`](https://github.com/Kitware/QuickView/commit/eb030a3a71058434c3dfaf8a126fa20cdb1d5df9))

- **camera**: Reset camera after variable loading
  ([`81292af`](https://github.com/Kitware/QuickView/commit/81292afb7b16288ba281a9243468cfcee0d56c2d))

- **color_range**: Support scientific notation
  ([`8dbaf00`](https://github.com/Kitware/QuickView/commit/8dbaf0033b8b4e71eebb8f2918575102711ca50d))

- **doc**: Add keyboard shortcut
  ([`a057eb3`](https://github.com/Kitware/QuickView/commit/a057eb3ae24fc7a730192591f9ccd5dcef6072a3))

- **esc**: Collapse large drawer
  ([`427c60d`](https://github.com/Kitware/QuickView/commit/427c60d545840f3d685c8acd4952a7a522d84c37))

- **exec**: Expose alias for application exec
  ([`0151840`](https://github.com/Kitware/QuickView/commit/01518403f0cd9fba0c05ffacc00217dae0460ef1))

- **hotkey**: Show hotkey on tools
  ([`5453e8c`](https://github.com/Kitware/QuickView/commit/5453e8c6c778e04205be4265455e87e4076bea2b))

- **import**: Set variables_loaded on import
  ([`7e9d31a`](https://github.com/Kitware/QuickView/commit/7e9d31a09db2e5f0a2343cf20dd4c50c2df680bf))

- **interaction**: Prevent rotation on top-right corner
  ([`3f89e0b`](https://github.com/Kitware/QuickView/commit/3f89e0bec11510c8aa5946506eae964490ac97c4))

- **lock**: Reduce icon size
  ([`f29c629`](https://github.com/Kitware/QuickView/commit/f29c629a04ca158b4efdeaaa68ef68ef464c8784))

- **logo**: Use same logo
  ([`2a97c15`](https://github.com/Kitware/QuickView/commit/2a97c156ec578b22d8c7c1a965d05dc084f212aa))

- **shortcuts**: Add projection shortcuts
  ([`d0bbec7`](https://github.com/Kitware/QuickView/commit/d0bbec7048105c8d6194c0703f3498e31e6905e9))

- **size**: Add auto flow option to support 5
  ([`71bac0c`](https://github.com/Kitware/QuickView/commit/71bac0c4af1ea2faf7d3ba08f1cb3fae96a1b6dc))

- **state**: Add missing layout info
  ([`a480dc0`](https://github.com/Kitware/QuickView/commit/a480dc053f6c028f8e5d1cf892dfdd9c00765681))

- **steps**: Reorder steps and add tooltip
  ([`f671910`](https://github.com/Kitware/QuickView/commit/f671910a040c692377382c05221891bd290cef06))

- **swap**: Sorted list of field to swap with
  ([`c3fa707`](https://github.com/Kitware/QuickView/commit/c3fa7073280d77598b01b4be3c283b95eb9f9e5d))

- **swap**: Swap order and size
  ([`6b31f36`](https://github.com/Kitware/QuickView/commit/6b31f3622ad742ca6abade08f630354771f1352b))

- **tauri**: Remove 2s wait at startup
  ([`926ff74`](https://github.com/Kitware/QuickView/commit/926ff746a344a9b030b78682c93ec39fedc7801e))

- **tauri**: Remove hot_reload and update css
  ([`8124604`](https://github.com/Kitware/QuickView/commit/8124604214e87e7421d83914f235974dece45d5f))

- **tauri**: Remove http from trame server
  ([`ee64795`](https://github.com/Kitware/QuickView/commit/ee64795a3929805a6da86b98141958a2d1543943))

- **tauri**: Use user home as file browser start
  ([`b705582`](https://github.com/Kitware/QuickView/commit/b7055821947c5270088e9445ca9920cdadbb78ef))

- **topPadding**: Better size handling
  ([`58389e5`](https://github.com/Kitware/QuickView/commit/58389e5694ddb8b5d2cff2fa3fd4914280a3a5de))

- **ui**: Better scrolling handling
  ([`442fc2f`](https://github.com/Kitware/QuickView/commit/442fc2f4b762507ecac3205885a1f0ab4e2dbaa9))

### Chores

- **ci**: Automatic release creation, packaging, and publishing
  ([`e9a09ee`](https://github.com/Kitware/QuickView/commit/e9a09eeb8f288ebc31e9e80abe7148a361c52f04))

### Continuous Integration

- Use hatchling for bundling app
  ([`6708bc7`](https://github.com/Kitware/QuickView/commit/6708bc7bf16f628272f0404846cf1bfd9288ad64))

- **test**: Fix test command
  ([`9203e07`](https://github.com/Kitware/QuickView/commit/9203e070062caa825e83864018e9056610aab036))

### Documentation

- Add app image on readme
  ([`f5b1340`](https://github.com/Kitware/QuickView/commit/f5b13405a57dc453279ca3352e4cfaff0aad87e6))

- **landing**: Add landing page
  ([`c8b9964`](https://github.com/Kitware/QuickView/commit/c8b99649e7d479bebbdc7b57b2a8a155c121ac20))

- **readme**: Use absolute link
  ([`399655f`](https://github.com/Kitware/QuickView/commit/399655f3829704af6b8fa2928df9fbf9a78669ee))

### Features

- Lut/size/order/import/export
  ([`00ce9d1`](https://github.com/Kitware/QuickView/commit/00ce9d141fd7b34c56fb16218a22902fb05c8c94))

- **animation**: Enable animation
  ([`c72b368`](https://github.com/Kitware/QuickView/commit/c72b3685d7f51d55c60fb5b0dc936fd05f8b2271))

- **colormap**: Add color blind safe filter
  ([`5c998ee`](https://github.com/Kitware/QuickView/commit/5c998eebe030a57f63f29d631af7892a959c395e))

- **file**: Add file handling in webui
  ([`dcf2725`](https://github.com/Kitware/QuickView/commit/dcf2725b5226a5ea05cd2715023f8670dd9bb622))

- **keyboard**: Add keyboard shortcuts
  ([`be265e1`](https://github.com/Kitware/QuickView/commit/be265e11d529133e0fcd147067ffa826b257aaf5))

- **offset**: Add logic to add gaps
  ([`3662fea`](https://github.com/Kitware/QuickView/commit/3662feac653766078c0448f299e78e6aea762ac6))

- **rendering**: Add initial layout handler
  ([`4de576d`](https://github.com/Kitware/QuickView/commit/4de576d75688a9d6a7d7ae7fda57bd8976fa766d))

- **vue3**: Update ui
  ([`2bcb7df`](https://github.com/Kitware/QuickView/commit/2bcb7df22097c971279395aef756c9d6fc60c112))

### Refactoring

- Major code cleanup
  ([`8298a55`](https://github.com/Kitware/QuickView/commit/8298a55e5d57d47ddc307a856f3d33f7f0f8b79f))

- **cleanup**: Gather js code into utils
  ([`dbc3cb2`](https://github.com/Kitware/QuickView/commit/dbc3cb2df39abec32c958085c495157f1fefff62))


## v1.0.2 (2025-09-16)

### Bug Fixes

- Add explicit reminder to quarantine
  ([`baf210e`](https://github.com/Kitware/QuickView/commit/baf210e8ea8322a746e50f5cd5a6a2475eb8ed9c))

- Adding Grid refactor and tauri/browser detection
  ([`ae8e523`](https://github.com/Kitware/QuickView/commit/ae8e5231c348af8286da6bb2ac69d8b1d5a3d13a))

- Check for tauri
  ([`f35fc41`](https://github.com/Kitware/QuickView/commit/f35fc4111ce5d91544bd542c6b08ff51bbc7e27f))

- Close view refactor and save screenshot w/ Tauri
  ([`4e21084`](https://github.com/Kitware/QuickView/commit/4e21084867669de06c0c1affa34c6a1a3e4b47dc))

- Preserve resizing and reposition of layout after closing one
  ([`87e5ae7`](https://github.com/Kitware/QuickView/commit/87e5ae710ee73409f26fe27fbf564222aa8f7a4e))

- Simply save screenshot logic
  ([`74f1e5c`](https://github.com/Kitware/QuickView/commit/74f1e5c88c82723f34754c2d0143e2c36f7e101b))

### Documentation

- Update for_app_developers.md
  ([`18503ff`](https://github.com/Kitware/QuickView/commit/18503ff8776da18f88d5574b11a2162f25593d79))

### Features

- Initial crude save screenshot
  ([`1dd938d`](https://github.com/Kitware/QuickView/commit/1dd938d8c57f48001b8063a1ceef4377c7107786))

- Multiple features and fixes
  ([`da9d7d7`](https://github.com/Kitware/QuickView/commit/da9d7d794fd37ee6b4c49049b0f33f1ca33cc276))


## v1.0.1 (2025-08-28)

### Bug Fixes

- Fixing close view issues
  ([`57f2e51`](https://github.com/Kitware/QuickView/commit/57f2e51be55a0df8872ea62f0172a6c60578cd80))

- Make average return type trame friendly
  ([`71a1cc7`](https://github.com/Kitware/QuickView/commit/71a1cc7b05c01490d4ae5a3cbbcd2bd7627f05a3))

- Remove unnecessary print and change TrameApp to app instead of
  ([`27d0888`](https://github.com/Kitware/QuickView/commit/27d08888f9e063d37619f0088baffe5136689c98))

### Documentation

- Correct a screenshot filename in toolbar.md
  ([`bfca581`](https://github.com/Kitware/QuickView/commit/bfca5811799d2f7a7a18c81e0c1a4efe0166bf59))

### Features

- Adding close button for views
  ([`18604bc`](https://github.com/Kitware/QuickView/commit/18604bc2bd658e2b3f420d9249387e62db29162f))


## v1.0.0 (2025-08-25)

### Bug Fixes

- Adding updated logo
  ([`40d5e22`](https://github.com/Kitware/QuickView/commit/40d5e22c3506be1d279fe839610796445a856a00))


## v0.1.21 (2025-08-25)

### Bug Fixes

- Bug fixes and minor features
  ([`db84432`](https://github.com/Kitware/QuickView/commit/db84432725a588d054fdf947e26c2ccde530733b))

### Documentation

- Add back pointer to Mark's script
  ([`f99ae67`](https://github.com/Kitware/QuickView/commit/f99ae673897309acb3ed0df9f30be1ee84bc69b9))

- Data requirement and misc
  ([`917a684`](https://github.com/Kitware/QuickView/commit/917a684fe35bb5cc2ca073f78dcdc55ccc37e2b7))

- Further revise toolbar description
  ([`7b5d2c0`](https://github.com/Kitware/QuickView/commit/7b5d2c0e74e6ebb326c1ea6394f3d2726d089dfe))

- Minor edit in doc homepage
  ([`345b5e8`](https://github.com/Kitware/QuickView/commit/345b5e816528250e5f7e81ac4180b5be611df93f))

- Minor edit in setup/for_end_users.md
  ([`847976d`](https://github.com/Kitware/QuickView/commit/847976d1cd7287822c0cf865dc1b7cc4df216718))

- Minor edits in future.md
  ([`571828a`](https://github.com/Kitware/QuickView/commit/571828a0dd5baa098d3870e81267632ec51dc37a))

- Misc small edits
  ([`b0a9364`](https://github.com/Kitware/QuickView/commit/b0a9364e5257ccc775d5ecdbfdb20d4733911530))

- Partial revision of toolbar page
  ([`0349513`](https://github.com/Kitware/QuickView/commit/0349513fff22a6065db1d23752d1f41ace3ee31c))

- README pages and plans page
  ([`ad964a8`](https://github.com/Kitware/QuickView/commit/ad964a8c8a227eed13b4ffc533dcafd6498ac81e))

- Revise and clean up pages on install and launch
  ([`e5e07ea`](https://github.com/Kitware/QuickView/commit/e5e07ea5750f497bac31eb7c229834b396968a68))

- Revise setup/for_end_users.md (quarantine and misc)
  ([`93e66aa`](https://github.com/Kitware/QuickView/commit/93e66aa6d65e5209838924cc74be3dc9c467c912))

- Slice selection and map projection
  ([`3d41099`](https://github.com/Kitware/QuickView/commit/3d410996365f8f527ca129a76e30a9c279640e73))

- Update all-version DOI's for Zenodo archives
  ([`cdb826a`](https://github.com/Kitware/QuickView/commit/cdb826a27e2523633f17ae280e049dd9fcef3fb7))

- Update control panel description; rename screenshots
  ([`05777ee`](https://github.com/Kitware/QuickView/commit/05777ee0860a90d02e849ddeb0a04893e590a196))

- Update GUI overview
  ([`989f190`](https://github.com/Kitware/QuickView/commit/989f190f3118a2af4f2605831c3237eb4b03f1a3))

- Update installation pages
  ([`382567b`](https://github.com/Kitware/QuickView/commit/382567b4236503ab08ec0670ff2c0dc7c8c0a2cf))

- Update README files; add state file for image
  ([`1853530`](https://github.com/Kitware/QuickView/commit/1853530a862178c76f2fd6ec085bf2e4df363552))

- Update reminders page
  ([`0084b95`](https://github.com/Kitware/QuickView/commit/0084b951a85d7827e8cd031b4e8c7de62fded82a))

- Update slice section screenshot for lat/lon sliders
  ([`3dc6c90`](https://github.com/Kitware/QuickView/commit/3dc6c9073714a9c951f0da3e4989d7841dbcbc60))

- Update toolbar page and images
  ([`835471a`](https://github.com/Kitware/QuickView/commit/835471ab64460367776fee900936235c6497abc8))

- Update userguide/connectivity.md
  ([`a5c90a6`](https://github.com/Kitware/QuickView/commit/a5c90a68ce81991af150b3d720878c70aaaa7c67))

- Update userguide/data_requirements.md
  ([`c0e9757`](https://github.com/Kitware/QuickView/commit/c0e97575e3006dae0c7ea0dd2e96c6c7af0ffd9b))

- Update viewport description
  ([`6b2dabe`](https://github.com/Kitware/QuickView/commit/6b2dabec8fff73d3540eeab4a6192cd3a5e15798))

- Update viewport description and screenshots; include state files
  ([`1a4c518`](https://github.com/Kitware/QuickView/commit/1a4c518c49c3cad2d16b86cfa0186cc2b17450ef))

- Variable selection
  ([`261e0c3`](https://github.com/Kitware/QuickView/commit/261e0c379417d40f4ebcf37ac80e34c3403614da))

- Viewport description
  ([`fbd88e7`](https://github.com/Kitware/QuickView/commit/fbd88e75dae0847c9ac17c7bc5ff8a8dae2edc68))


## v0.1.20 (2025-08-24)

### Bug Fixes

- Clear layout/registry by triggering pipeline invalid on state load
  ([`a904837`](https://github.com/Kitware/QuickView/commit/a904837c30beeb380d296f715848a7472f397f80))

- Moving busy icon to title
  ([`d7c7f0c`](https://github.com/Kitware/QuickView/commit/d7c7f0ce754e6066473cf55d5f2b654e25bd9095))

- P0 variable in reader and move camera controls to toolbar
  ([`834dbe7`](https://github.com/Kitware/QuickView/commit/834dbe7d786a9ef591a67231b5bdcb71bea484ed))

- Progress icon resize disable
  ([`d344235`](https://github.com/Kitware/QuickView/commit/d344235b7d8adc6122e40192d3bff8673ba605b5))


## v0.1.19 (2025-08-23)

### Bug Fixes

- Adding missing_value handling in reader
  ([`8cc4705`](https://github.com/Kitware/QuickView/commit/8cc47052e2ea5a2e2c7a57c33538525ce4903249))

- Broken interactive camera viewport adjustment
  ([`0185508`](https://github.com/Kitware/QuickView/commit/01855089d347ad7080552539b48ac76f8042015e))

- Loading bar and icon size
  ([`aafae33`](https://github.com/Kitware/QuickView/commit/aafae3377ed4e434726144a1738350b142bb69b5))


## v0.1.18 (2025-08-22)


## v0.1.17 (2025-08-22)

### Bug Fixes

- Color map issue
  ([`ab2cb68`](https://github.com/Kitware/QuickView/commit/ab2cb68a91c2110d7cbdb152166fcee0dc9d1c51))

- Color settings apply to load state
  ([`8a51620`](https://github.com/Kitware/QuickView/commit/8a516206e4c4756b87fa2ccca0127070216ce8b8))

- Remove print statements
  ([`8eb6b56`](https://github.com/Kitware/QuickView/commit/8eb6b56634f1ebf859d3c6bed60eeb3d0b3c3e13))

- Usability fixes
  ([`25a9c30`](https://github.com/Kitware/QuickView/commit/25a9c3025f107623b2b5a28f6e139c790bd919a0))


## v0.1.16 (2025-08-21)

### Bug Fixes

- Only build dmg for now
  ([`473f8f3`](https://github.com/Kitware/QuickView/commit/473f8f385e4b405240e98eab0250d6f40fd55b34))

### Documentation

- Correct filenames for toolbar screenshots
  ([`8a6b8d5`](https://github.com/Kitware/QuickView/commit/8a6b8d5f2d1b5892176fb49b8331d69514b7fded))

- Gui overview
  ([`4f5ec53`](https://github.com/Kitware/QuickView/commit/4f5ec5373f554d7a5183e89f967217a35269ac23))

- Minor edits
  ([`d622517`](https://github.com/Kitware/QuickView/commit/d622517947ec1a3309b6c4558ffed5da5f79ecf1))

- Placeholder for camera widget description
  ([`2743299`](https://github.com/Kitware/QuickView/commit/2743299d8c64079f27cd3e96573164ed34782762))

- Toolbar description and misc updates
  ([`40c9677`](https://github.com/Kitware/QuickView/commit/40c9677b764aaa08fe237277a47d61b7539af933))

- Updates on quick start, connectivity, etc. add page on plans
  ([`6e25333`](https://github.com/Kitware/QuickView/commit/6e253330c8b9e6b94f8198d936d8fed9ebae8c70))


## v0.1.15 (2025-08-21)

### Bug Fixes

- Changing splash screen to white
  ([`59b943f`](https://github.com/Kitware/QuickView/commit/59b943fdb64614535fb485717f3971a7e9afa19a))

- Clear varaible selection
  ([`1d02c67`](https://github.com/Kitware/QuickView/commit/1d02c67bd910e26e52802b049e19eb91ea8447f8))

- Coloring of load data button
  ([`c2dc098`](https://github.com/Kitware/QuickView/commit/c2dc0981412459e24f37f80a86cae1573eaa6dd3))

- Getting rid of the timekeeper
  ([`677cd7b`](https://github.com/Kitware/QuickView/commit/677cd7b7e9f671b2cb9b5f7b224516d6f233d601))

- Missing color bars
  ([`e7d427e`](https://github.com/Kitware/QuickView/commit/e7d427e29bbaa751e5b7ee171d2b63cf3e30f780))

- Usability changes
  ([`93392a3`](https://github.com/Kitware/QuickView/commit/93392a34b203b689b6ab32e686fec4e8314b7a69))


## v0.1.14 (2025-08-20)

### Bug Fixes

- Camera reset logic to be less complicated
  ([`fc4247a`](https://github.com/Kitware/QuickView/commit/fc4247a3fe03bff31458ef0802d6250d31696d30))


## v0.1.13 (2025-08-18)

### Bug Fixes

- Adding icon and version to title
  ([`8826080`](https://github.com/Kitware/QuickView/commit/88260809011da430e55a4d688e1d4773befb28df))

- README -- add note about data
  ([`912bfad`](https://github.com/Kitware/QuickView/commit/912bfad03d2ebd98668f06fc9f8c66c6dee10eea))

- Update readme
  ([`55a79e2`](https://github.com/Kitware/QuickView/commit/55a79e2d0b26dbb49e6ca1255aa4814b563dc5b6))

### Chores

- Refactor utilities classes
  ([`6f058a9`](https://github.com/Kitware/QuickView/commit/6f058a95a1809cc60a38b61064f3bab01e6dea53))


## v0.1.12 (2025-08-17)

### Bug Fixes

- Camera reset issue -- maximize view port utilization
  ([`73786c9`](https://github.com/Kitware/QuickView/commit/73786c998bda413845ec99625abb48ec2d7b0f24))

- Package only dmg for now
  ([`48db7bf`](https://github.com/Kitware/QuickView/commit/48db7bff03ad9eedede246cc71958455cc4ef8f7))

- Splashscreen changes
  ([`ec45d05`](https://github.com/Kitware/QuickView/commit/ec45d05e99d8e8bccafa8bb0440f126425fa06b9))

- Tauri DPI issue and color properties simplified handling
  ([`79b038c`](https://github.com/Kitware/QuickView/commit/79b038c498020a5075f0ebeb44cc13af07e7bcc1))

- Update dpi issues with packaged app
  ([`2270564`](https://github.com/Kitware/QuickView/commit/2270564d71157dd10f079937f44c37727acc006d))


## v0.1.11 (2025-08-15)

### Bug Fixes

- CI for release improper changelog
  ([`a335715`](https://github.com/Kitware/QuickView/commit/a335715029b91076f1b8b069cfd10ea1657cb4f6))

### Chores

- Cleanup root and update README
  ([`cb82275`](https://github.com/Kitware/QuickView/commit/cb8227539080291abf35090fdb9333fd9ef5d747))

- New colormaps, splashscreen logos, and drop packaging tar.gz
  ([`ff034ea`](https://github.com/Kitware/QuickView/commit/ff034ea352ce2fdc9f33b53d9e8dc09bd2d4f718))


## v0.1.10 (2025-08-13)

### Bug Fixes

- Adding changes to update UI after file changes
  ([`d58a930`](https://github.com/Kitware/QuickView/commit/d58a9300bfbbbdc975ab9c5d0be089e4ff63fbd1))

- Update UI when changing data files
  ([`8024f9d`](https://github.com/Kitware/QuickView/commit/8024f9d8a134b7c6743a0ce529dfada9b7efe928))

### Features

- Adding loading bar to splash screen
  ([`993c855`](https://github.com/Kitware/QuickView/commit/993c8553903448c8ac3cc202c45f35a6950279b2))


## v0.1.9 (2025-08-11)

### Bug Fixes

- **Hui Review**: Batch fix issues
  ([`f903060`](https://github.com/Kitware/QuickView/commit/f903060d453dd2be5e811e85e3b401a5de1ea1bc))

- **optimize reader**: Optimize the EAM Slice Reader
  ([`c257aad`](https://github.com/Kitware/QuickView/commit/c257aad44932b2aa63fb826970f5b39d76e16ccd))


## v0.1.8 (2025-08-01)


## v0.1.7 (2025-08-01)


## v0.1.6 (2025-07-30)

### Features

- **floating scalar bar**: Adding changes to make the scalar bar floating
  ([`7b6c699`](https://github.com/Kitware/QuickView/commit/7b6c6990c4a71eb6feb08eda6440d26753978c4f))


## v0.1.5 (2025-07-28)

### Features

- Replace ParaView scalar bar with custom HTML colorbar
  ([`900ce4c`](https://github.com/Kitware/QuickView/commit/900ce4c9abecff825c6d14a13ec971def0452682))

### Refactoring

- Replace EventType enum with direct method calls for color settings
  ([`cf42dca`](https://github.com/Kitware/QuickView/commit/cf42dcad1b066a027c1a33d4cd50b02316d350ea))


## v0.1.4 (2025-07-28)


## v0.1.3 (2025-07-21)

### Bug Fixes

- Use unfiltered variable lists in load_variables to include all selections
  ([`d56ba31`](https://github.com/Kitware/QuickView/commit/d56ba3134973dadcea1fd62f4f1f39acabac34e9))


## v0.1.2 (2025-07-11)

### Bug Fixes

- Improve toolbar responsiveness and prevent button hiding on resize
  ([`477752a`](https://github.com/Kitware/QuickView/commit/477752a7c5f129d3b403071363dab4ecc1188470))

- Remove git tagging from package-and-release workflow
  ([`843ef8a`](https://github.com/Kitware/QuickView/commit/843ef8a36c2d74fca983a3b9e06eb6b74c34eca7))

### Refactoring

- Simplify grid layout tracking using variable names as keys
  ([`1c8b935`](https://github.com/Kitware/QuickView/commit/1c8b935969c65cd3c336b10ebaf6f103e8626a80))


## v0.1.1 (2025-07-09)

### Bug Fixes

- Add debugging and improve bump2version output handling
  ([`5ad6d2d`](https://github.com/Kitware/QuickView/commit/5ad6d2d20ee5e0bb907ad3b705b0ea1ddba151f8))

- Add Git LFS support to workflows and revert view_manager changes
  ([`b2b8e2a`](https://github.com/Kitware/QuickView/commit/b2b8e2ac729a979ae8402122e3fbd323583d550e))

- Correct syntax errors in release.sh script
  ([`232df08`](https://github.com/Kitware/QuickView/commit/232df0805480f93cdebeb648fb128a5f3f51c94f))

- Only push new tag instead of all tags in release script
  ([`079b134`](https://github.com/Kitware/QuickView/commit/079b134e89b170bc36c9f7a2bc681b4f966de0d4))

- Only push the new tag and handle existing tags gracefully
  ([`1bbebc9`](https://github.com/Kitware/QuickView/commit/1bbebc9bff4fd088239a8dbe28a20d05736117dc))

- Redirect status messages to stderr in release script
  ([`35428ac`](https://github.com/Kitware/QuickView/commit/35428ac48a7c551dbb2570e3020c44a288e50d7c))

- Update create-release-pr workflow for better flexibility
  ([`e7d56d3`](https://github.com/Kitware/QuickView/commit/e7d56d38cfba0a766345f1dd9b8b42d75c830eae))

- Update README badges to point to correct repository and workflows
  ([`d47514e`](https://github.com/Kitware/QuickView/commit/d47514e2ebf5b3c0c5a7844d7cba3058863ddd72))

- Update release script to handle bump2version tag creation
  ([`1c0ed6c`](https://github.com/Kitware/QuickView/commit/1c0ed6c34550026349dc89aa91138d1319b18972))

- Use bump2version --list to get clean version output
  ([`56bb0df`](https://github.com/Kitware/QuickView/commit/56bb0df6ef5d1ea614faaaccc1854b69eb9ac91d))

### Refactoring

- Remove create-release-pr workflow and clean up release.sh
  ([`422d483`](https://github.com/Kitware/QuickView/commit/422d48332faad82e21b2bd46ddb9955414fd2ed8))


## v0.1.0 (2025-07-09)

- Initial Release
