# Каталог бесплатных ресурсов для игр

Проверено 2026-11-24. Файл собирает `scripts/asset_catalog.py markdown`, руками не править.

Перед выпуском игры лицензию каждой вещи читать ещё раз (навык `asset-licensing`).

## Где брать

### Персонажи

| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |
|---|---|---|---|---|---|---|---|
| [Human Base Meshes 1.4.1](https://download.blender.org/demo/asset-bundles/human-base-meshes/) | Реалистичные и стилизованные тела, головы, кисти, стопы, череп, скелет | 3D | по ссылке | README: CC0 | да | файлы набора | Внутри файла есть чужой текст лицензии (Rain Rig, CC BY 4.0): указывать Blender Foundation |
| [Blender Studio characters](https://studio.blender.org/characters/) | Готовые персонажи с ригом из фильмов | 3D | нужен вход | Обычно CC BY 4.0, смотреть у каждого | проверить | страница не открывалась | Узнаваемые персонажи фильмов: в игру не брать |
| [MPFB 2 и паки MakeHuman](https://static.makehumancommunity.org/assets/assetpacks.html) | Генератор людей: тело, лицо, кожа, волосы, одежда, скелет Mixamo | 3D | по ссылке | Ядро CC0; паки CC0 или CC BY | да | файлы набора | См. список avoid: AGPL в заголовках и чужие персонажи |
| [CharMorph](https://github.com/Upliner/CharMorph) | Генератор персонажей для Blender | 3D | по ссылке | Код GPL-3.0, часть данных AGPL-3.0 | проверить | страница сайта | Проверять лицензию каждой базы тела |
| [Anny (NAVER)](https://github.com/naver/anny) | Параметрическое тело на данных MPFB | 3D | по ссылке | Код Apache-2.0, данные CC0; топология SMPL-X некоммерческая | проверить | страница сайта | Не включать smplx и догружаемые некоммерческие данные |
| [MetaHuman](https://www.metahuman.com/) | Реалистичные люди Epic | 3D | нужен вход | Лицензия Epic | проверить | страница не открывалась | Читать действующую лицензию |
| [VRoid Studio](https://vroid.com/en/studio) | Аниме-персонажи | 3D | нужен вход | Условия VRoid | проверить | страница не открывалась | Аниме-стиль |
| [Daz Studio](https://www.daz3d.com/interactive-license-info) | Много одежды и поз | 3D | нужен вход | Для игр нужна отдельная Interactive License | только платно | страница сайта | Без Interactive License в игру нельзя |

### Анимации

| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |
|---|---|---|---|---|---|---|---|
| [Mixamo](https://www.mixamo.com/) | Больше 2400 клипов и авториг | 3D | нужен вход | Условия Adobe | да | страница не открывалась | Сырые клипы не раздавать |
| [Universal Animation Library 1 и 2](https://opengameart.org/content/universal-animation-library) | Больше 250 клипов | 3D | по ссылке | CC0 1.0 | да | страница сайта | Имена костей в 1 и 2 разные |
| [CMU Motion Capture](http://mocap.cs.cmu.edu/) | Больше 2500 записей движения | 3D | по ссылке | Свободное использование, условия на сайте | проверить | страница открыта, лицензия не подтверждена | Нужна чистка |
| [100STYLE](https://www.ianxmason.com/100style/) | 100 стилей ходьбы и бега, BVH | 3D | по ссылке | CC BY 4.0 | да | страница сайта |  |
| [LAFAN1 (Ubisoft)](https://github.com/ubisoft/ubisoft-laforge-animation-dataset) | Захват движения | 3D | по ссылке | CC BY-NC-ND 4.0 | не брать | страница сайта | Некоммерческая |
| [Bandai Namco Motion Dataset](https://github.com/BandaiNamcoResearchInc/Bandai-Namco-Research-Motiondataset) | Захват движения | 3D | по ссылке | Исследовательская, читать LICENSE | не брать | страница открыта, лицензия не подтверждена | Обычно некоммерческая |
| [ActorCore Free](https://actorcore.reallusion.com/free) | Бесплатные клипы Reallusion | 3D | нужен вход | Лицензия Reallusion | проверить | страница открыта, лицензия не подтверждена |  |
| [MoCap Online Free](https://mocaponline.com/collections/free-animations) | Пробные клипы | 3D | нужен вход | Своя | проверить | страница не открывалась |  |
| [Rokoko Free Mocap](https://www.rokoko.com/) | Бесплатные клипы | 3D | нужен вход | Своя | проверить | страница не открывалась |  |
| [Cascadeur](https://cascadeur.com/plans) | Анимация с физикой | 3D | нужен вход | Бесплатный тариф некоммерческий | только платно | страница сайта | Для продажи нужен платный тариф |

### Модели

| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |
|---|---|---|---|---|---|---|---|
| [Charge Open Movie Library](https://extensions.blender.org/add-ons/charge/) | Предметы, материалы и эффекты из фильма Blender Studio | 3D | внутри Blender | CC0 1.0 | да | страница сайта | Найти charge в Get Extensions |
| [Sketchfab (фильтр Downloadable и лицензия)](https://sketchfab.com/features/free-3d-models) | Самый большой каталог, есть латы и шлемы музеев | 3D | нужен вход | У каждой модели своя: CC0, CC BY, CC BY-SA, NC, Editorial | проверить | страница сайта | Брать CC0 и CC BY; не брать NC, ND, Editorial, чужих персонажей |
| [Fab (Epic)](https://www.fab.com/) | Магазин, раздаёт бесплатное | 3D | нужен вход | Fab Standard License или CC BY | проверить | страница сайта | Читать лицензию вещи |
| [BlenderKit](https://www.blenderkit.com/) | Библиотека внутри Blender | 3D | нужен вход | CC0 или Royalty Free | да | страница сайта | RF: сами модели не перепродавать |
| [Blend Swap](https://blendswap.com/) | 26 тысяч файлов .blend | 3D | нужен вход | CC0, CC BY, CC BY-SA и другие | проверить | страница сайта |  |
| [Poly Pizza](https://poly.pizza/) | Низкополигональные модели, архив Google Poly | 3D | по ссылке | CC0 и CC BY у каждой | да | страница открыта, лицензия не подтверждена | Мультяшный стиль |
| [Three D Scans](https://threedscans.com/) | Сканы скульптур музеев | 3D | по ссылке | Заявлено без авторских прав, на странице не подтверждено | проверить | страница открыта, лицензия не подтверждена |  |
| [Smithsonian Open Access 3D](https://3d.si.edu/cc0) | Сканы музейных вещей | 3D | скачивает человек | CC0 у отмеченных | проверить | страница не открывалась | Сайт не пускает программы |
| [NASA 3D Resources](https://science.nasa.gov/3d-resources/) | Космос | 3D | по ссылке | Материалы NASA | проверить | страница открыта, лицензия не подтверждена | Логотип NASA не использовать |
| [Khronos glTF Sample Assets](https://github.com/KhronosGroup/glTF-Sample-Assets) | Проверочные модели glTF | 3D | по ссылке | У каждой своя | проверить | страница сайта | Для тестов движка |
| [TurboSquid Free](https://www.turbosquid.com/Search/3D-Models/free) | Бесплатный раздел магазина | 3D | нужен вход | TurboSquid Royalty Free, есть Editorial | проверить | страница сайта | Editorial не брать |
| [CGTrader Free](https://www.cgtrader.com/free-3d-models) | Бесплатный раздел магазина | 3D | нужен вход | Своя Royalty Free, есть Editorial | проверить | страница сайта |  |
| [Objaverse](https://objaverse.allenai.org/) | Огромный набор с Sketchfab | 3D | по ссылке | У каждой модели своя | проверить | страница сайта | Только с проверкой каждой модели |
| [Quaternius](https://quaternius.com/) | Модульные наряды, базовые тела, 2 библиотеки анимаций, окружение | 3D, 2.5D | скачивает человек | CC0 или QAL (без прямой перепродажи) | да | страница сайта | Стилизованный низкополигональный; с itch.io скачивает человек |
| [KayKit](https://github.com/KayKit-Game-Assets) | Персонажи, скелеты, подземелье, гексы | 3D, 2.5D | по ссылке | CC0 1.0 | да | файлы набора | Мультяшный |
| [Kenney](https://kenney.nl/assets) | Больше 100 наборов | 2D, 2.5D, 3D | скачивает человек | CC0 1.0 | да | страница сайта | Кнопка скачивания в браузере; часть есть на OpenGameArt |

### Материалы

| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |
|---|---|---|---|---|---|---|---|
| [Poly Haven Lite (онлайн-библиотека Blender)](https://extensions.blender.org/add-ons/poly-haven/) | Poly Haven прямо в браузере ресурсов | 3D | внутри Blender | CC0 1.0 | да | страница сайта | Найти poly_haven в Get Extensions |
| [ambientCG Lite (онлайн-библиотека Blender)](https://extensions.blender.org/add-ons/ambientcg/) | ambientCG прямо в браузере ресурсов | 3D | внутри Blender | CC0 1.0 | да | страница сайта | Найти ambientCG в Get Extensions |
| [Poly Haven](https://polyhaven.com/) | 871 текстура, 522 модели, 999 HDRI в каталоге | 3D | по ссылке | CC0 1.0 | да | страница сайта | Не выкачивать всё подряд; для Blender удобнее их библиотека |
| [ambientCG](https://ambientcg.com/) | 2046 материалов до 8K и выше | 3D | по ссылке | CC0 1.0 | да | страница сайта | API v2: https://ambientcg.com/api/v2/full_json |
| [cgbookcase](https://www.cgbookcase.com/) | PBR-текстуры | 3D | по ссылке | Заявлена CC0, на открытой странице не подтверждено | проверить | страница открыта, лицензия не подтверждена |  |
| [ShareTextures](https://www.sharetextures.com/) | PBR-текстуры | 3D | по ссылке | Своя версия CC0 с ограничениями | проверить | страница сайта | Читать ограничения на https://www.sharetextures.com/p/license |
| [TextureCan](https://www.texturecan.com/) | 650+ PBR-текстур | 3D | по ссылке | CC0 1.0 | да | страница сайта |  |
| [3D Textures](https://3dtextures.me/) | PBR-текстуры, в том числе стилизованные | 3D | по ссылке | CC0 | да | страница сайта |  |
| [FreePBR](https://freepbr.com/) | PBR-материалы | 3D | скачивает человек | Своя лицензия | проверить | страница открыта, лицензия не подтверждена | Для продажи бывает нужна платная лицензия |
| [Texture Ninja](https://texture.ninja/) | Фототекстуры | 2D, 3D | по ссылке | Заявлена свободной, не подтверждено | проверить | страница открыта, лицензия не подтверждена |  |
| [LotPixel](https://www.lotpixel.com/) | Бесплатный раздел PBR | 3D | нужен вход | Своя лицензия, бесплатное можно коммерчески | да | страница сайта |  |
| [Poliigon](https://www.poliigon.com/) | Часть материалов бесплатна | 3D | нужен вход | Своя лицензия | проверить | страница открыта, лицензия не подтверждена |  |
| [Pixar One Twenty Eight](https://renderman.pixar.com/pixar-one-twenty-eight) | 128 повторяющихся текстур | 2D, 3D | по ссылке | CC BY 4.0 | да | страница сайта |  |

### Свет (HDRI)

| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |
|---|---|---|---|---|---|---|---|
| [HDRMAPS Freebies](https://hdrmaps.com/freebies/) | Бесплатные HDRI | 3D | нужен вход | Своя лицензия | проверить | страница открыта, лицензия не подтверждена |  |
| [NoEmotionHDRs](http://noemotionhdrs.net/) | HDRI | 3D | по ссылке | CC BY-ND 4.0 | не брать | страница сайта | Запрещены изменённые версии |

### Эффекты

| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |
|---|---|---|---|---|---|---|---|
| [Unity Labs flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | 28 листов: огонь, дым, взрывы | 2D, 2.5D, 3D | по ссылке | CC0 1.0 | да | страница сайта |  |
| [JangaFX Free VDB](https://jangafx.com/software/embergen/download/free-vdb-animations) | Объёмные дым, огонь, взрывы | 3D | скачивает человек | CC0 | да | страница сайта |  |
| [PVFX Foundry](https://nerijs.itch.io/pvfx-foundry) | 253 пиксельных эффекта | 2D, 2.5D | скачивает человек | CC0 1.0 | да | страница сайта | Сделано с помощью ИИ: сверить с правилами площадки |
| [CodeManu VFX Free Pack](https://codemanu.itch.io/vfx-free-pack) | Взрывы, удары | 2D, 2.5D | скачивает человек | Противоречие: текст public domain, поле CC BY 4.0, на OpenGameArt CC0 | проверить | страница сайта | Безопаснее указать автора |
| [Effekseer](https://effekseer.github.io/en/) | Редактор эффектов с примерами | 2D, 3D | по ссылке | MIT (редактор); примеры смотреть отдельно | проверить | страница открыта, лицензия не подтверждена |  |
| [OpenVDB samples](https://www.openvdb.org/download/) | Образцы облаков и дыма | 3D | по ссылке | Смотреть у файла | проверить | страница открыта, лицензия не подтверждена |  |
| [Godot Shaders](https://godotshaders.com/) | Шейдеры | 2D, 3D | по ссылке | У каждого: CC0, MIT, GPL 3, Shadertoy | проверить | страница сайта | GPL и Shadertoy не брать без проверки |

### 2D и интерфейс

| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |
|---|---|---|---|---|---|---|---|
| [OpenGameArt](https://opengameart.org/art-search-advanced) | Свалка всего, фильтр по лицензии | 2D, 2.5D, 3D | по ссылке | У каждой вещи своя; брать CC0, CC BY | проверить | страница сайта | GPL и SA не мешать с закрытым кодом |
| [itch.io, фильтр CC0](https://itch.io/game-assets/assets-cc0) | 2945 наборов с пометкой CC0 | 2D, 2.5D, 3D | скачивает человек | CC0 у отмеченных | проверить | страница сайта | Страницы наборов открывает человек; смотреть пометку AI |
| [0x72 Dungeon Tileset II](https://0x72.itch.io/dungeontileset-ii) | Подземелье и герои | 2D | скачивает человек | CC0 1.0 | да | страница сайта | Пиксельный |
| [Ansimuz](https://ansimuz.itch.io/) | Фоны, персонажи, платформеры | 2D | скачивает человек | У каждого набора своя | проверить | страница открыта, лицензия не подтверждена | Пиксельный |
| [CraftPix Freebies](https://craftpix.net/freebies/) | Персонажи, тайлы, интерфейсы | 2D, 2.5D | нужен вход | Своя: в играх можно, исходники не перепродавать | да | страница сайта | https://craftpix.net/file-licenses/ |
| [Universal LPC Spritesheet Generator](https://liberatedpixelcup.github.io/Universal-LPC-Spritesheet-Character-Generator/) | Сборка 2D-героя по слоям одежды | 2D | по ссылке | CC BY-SA 3.0, GPL 3.0, OGA-BY по слоям | проверить | страница сайта | SA и GPL: сверять со своей лицензией; пиксельный |
| [game-icons.net](https://game-icons.net/) | Больше 4000 иконок SVG | 2D | по ссылке | CC BY 3.0, часть CC0 | да | файлы набора | Подпись авторов обязательна |
| [Tabler Icons](https://tabler.io/icons) | Иконки интерфейса | 2D | по ссылке | MIT | да | файлы набора |  |
| [Lucide](https://lucide.dev/) | Иконки интерфейса | 2D | по ссылке | ISC и MIT | да | страница сайта |  |
| [Phosphor Icons](https://phosphoricons.com/) | Иконки интерфейса | 2D | по ссылке | Заявлена MIT, на странице не подтверждено | да | страница открыта, лицензия не подтверждена |  |
| [Iconify](https://icon-sets.iconify.design/) | Поиск по сотням наборов иконок | 2D | по ссылке | У каждого набора своя | проверить | страница сайта |  |
| [Rijksmuseum data](https://data.rijksmuseum.nl/) | Картины и гравюры, доспехи и оружие для образцов | 2D | по ссылке | Большая часть общественное достояние | проверить | страница сайта |  |
| [Met Museum Open Access](https://www.metmuseum.org/art/collection) | Музейные фото, оружие и доспехи | 2D | по ссылке | CC0 у отмеченных Open Access | проверить | страница не открывалась |  |
| [Art Institute of Chicago](https://www.artic.edu/open-access/open-access-images) | Музейные фото | 2D | по ссылке | CC0 у отмеченных | проверить | страница не открывалась |  |
| [Openverse](https://openverse.org/) | Поиск картинок и звука со свободной лицензией | 2D | по ссылке | У каждой вещи своя | проверить | страница не открывалась |  |
| [Unsplash](https://unsplash.com/license) | Фото | 2D | нужен вход | Unsplash License | проверить | страница не открывалась | Узнаваемые люди и марки: нужны отдельные права |
| [Pexels](https://www.pexels.com/license/) | Фото и видео | 2D | нужен вход | Pexels License | проверить | страница не открывалась | Узнаваемые люди и марки: нужны отдельные права |

### Шрифты

| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |
|---|---|---|---|---|---|---|---|
| [Google Fonts](https://fonts.google.com/?subset=cyrillic) | Шрифты, фильтр Cyrillic | 2D | по ссылке | Чаще OFL 1.1 | да | файлы набора | Файлы: https://github.com/google/fonts |
| [Fontsource](https://fontsource.org/) | Шрифты пакетами npm | 2D | по ссылке | У каждого своя, чаще OFL | да | страница открыта, лицензия не подтверждена |  |

### Звуки

| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |
|---|---|---|---|---|---|---|---|
| [Freesound](https://freesound.org/) | Сотни тысяч звуков | 2D, 3D | нужен вход | CC0, CC BY, CC BY-NC у каждого | проверить | страница сайта | NC не брать |
| [Sonniss GameAudioGDC](https://sonniss.com/gameaudiogdc) | Десятки ГБ студийных звуков | 2D, 3D | скачивает человек | Своя: игры можно; раздавать звуки и обучать ИИ нельзя | да | страница сайта | Скачивание означает принятие договора, качает человек |
| [ZapSplat](https://www.zapsplat.com/) | Звуки и музыка | 2D, 3D | нужен вход | Своя: бесплатно с подписью | да | страница сайта |  |
| [Pixabay](https://pixabay.com/service/license-summary/) | Звуки, музыка, фото | 2D | скачивает человек | Pixabay License | проверить | страница не открывалась | Много сделанного ИИ |
| [National Park Service sounds](https://www.nps.gov/subjects/sound/gallery.htm) | Природа, животные | 2D, 3D | по ссылке | Общественное достояние | да | страница сайта |  |
| [BBC Sound Effects](https://sound-effects.bbcrewind.co.uk/licensing) | 33 тысячи звуков | 2D, 3D | скачивает человек | Бесплатно обычно только некоммерчески | не брать | страница открыта, лицензия не подтверждена |  |

### Музыка

| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |
|---|---|---|---|---|---|---|---|
| [Incompetech](https://incompetech.com/music/royalty-free/) | Музыка Kevin MacLeod | 2D, 3D | по ссылке | CC BY или платная без подписи | да | страница сайта |  |
| [ccMixter dig](https://dig.ccmixter.org/games) | Фильтр music for games и commercial use | 2D, 3D | по ссылке | CC BY и CC BY-NC | проверить | страница сайта | NC не брать |
| [Musopen](https://musopen.org/) | Классика | 2D, 3D | нужен вход | Общественное достояние и CC у записей | проверить | страница не открывалась |  |
| [FreePD](https://freepd.com/) | Сайт закрыт | 2D | закрыт | – | не брать | страница сайта | На 2026-11-24 сайт пишет, что отключён |

### Программы

| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |
|---|---|---|---|---|---|---|---|
| [Blender Extensions](https://extensions.blender.org/) | Около 1480 дополнений, тем и 8 онлайн-библиотек | 2D, 2.5D, 3D | внутри Blender | GPL и совместимые; библиотеки CC0 | да | страница сайта | Ставить из Blender: Preferences, Get Extensions |
| [Material Maker](https://www.materialmaker.org/) | Процедурные материалы | 2D, 3D | по ссылке | MIT | да | страница сайта | winget: RodZill4.MaterialMaker |
| [Krita](https://krita.org/) | Рисование и 2D-анимация | 2D | по ссылке | GPL-3.0 | да | каталог winget | winget: KDE.Krita |
| [GIMP](https://www.gimp.org/) | Редактор картинок | 2D | по ссылке | GPL-3.0 | да | каталог winget | winget: GIMP.GIMP.3 |
| [Inkscape](https://inkscape.org/) | Векторная графика | 2D | по ссылке | GPL-2.0 | да | каталог winget | winget: Inkscape.Inkscape |
| [Blockbench](https://www.blockbench.net/) | Низкополигональные модели | 2D, 2.5D, 3D | по ссылке | GPL-3.0 | да | каталог winget | winget: JannisX11.Blockbench |
| [Pixelorama](https://orama-interactive.itch.io/pixelorama) | Пиксель-арт и анимация | 2D | по ссылке | MIT | да | каталог winget | winget: OramaInteractive.Pixelorama |
| [LDtk](https://ldtk.io/) | Редактор уровней | 2D | по ссылке | MIT | да | каталог winget | winget: deepnight.LDtk |
| [Tiled](https://www.mapeditor.org/) | Редактор карт, в том числе изометрия | 2D, 2.5D | по ссылке | GPL-2.0+ | да | каталог winget | winget: Tiled.Tiled |
| [Laigter](https://azagaya.itch.io/laigter) | Карты нормалей для спрайтов | 2D, 2.5D | скачивает человек | Не проверено | проверить | страница не открывалась | В winget нет |
| [MeshLab](https://www.meshlab.net/) | Чистка и упрощение сеток | 3D | по ссылке | GPL-3.0 | да | каталог winget | winget: CNRISTI.MeshLab |
| [Upscayl](https://upscayl.org/) | Увеличение картинок | 2D | по ссылке | AGPL-3.0 | да | каталог winget | winget: Upscayl.Upscayl |
| [chaiNNer](https://chainner.app/) | Цепочки обработки картинок | 2D | по ссылке | GPL-3.0 | да | каталог winget | winget: chaiNNer-org.chaiNNer |
| [ImageMagick](https://imagemagick.org/) | Пакетная обработка картинок | 2D | по ссылке | ImageMagick License | да | каталог winget | winget: ImageMagick.ImageMagick |
| [Audacity](https://www.audacityteam.org/) | Редактор звука | 2D, 3D | по ссылке | GPL-3.0+ | да | каталог winget | winget: Audacity.Audacity |
| [LMMS](https://lmms.io/) | Создание музыки | 2D, 3D | по ссылке | GPL-2.0+ | да | каталог winget | winget: LMMS.LMMS |
| [glTF Transform](https://gltf-transform.dev/) | Подготовка моделей для веба | 3D | по ссылке | MIT | да | файлы набора | npm: @gltf-transform/cli |
| [gltfpack](https://meshoptimizer.org/gltf/) | Сжатие и упрощение моделей | 3D | по ссылке | MIT | да | файлы набора | npm: gltfpack |

## Конкретные наборы

Прямые ссылки на файлы лежат в `asset-packs.json`.

### Онлайн-библиотеки Blender: 5

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [Bradley Node Presets](https://extensions.blender.org/add-ons/bradley-nodes-presets/) | Focusing on the motion graphics and VFX aspects of node systems | extensions.blender.org | CC0-1.0 |  | id в Blender: bradley_nodes_presets, проверена версия 1.0.0 |
| [ambientCG Lite](https://extensions.blender.org/add-ons/ambientcg/) | Free 3D Assets for Everyone and Everything | extensions.blender.org | CC0-1.0 |  | id в Blender: ambientCG, проверена версия 1.0.0 |
| [Charge Open Movie Library](https://extensions.blender.org/add-ons/charge/) | Hard-surface objects from the film, materials and FX setups | extensions.blender.org | CC0-1.0 |  | id в Blender: charge, проверена версия 1.0.0 |
| [Poly Haven Lite](https://extensions.blender.org/add-ons/poly-haven/) | The Public 3D Asset Library | extensions.blender.org | CC0-1.0 |  | id в Blender: poly_haven, проверена версия 1.0.0 |
| [Cartesian Caramel's Everyday Nodes](https://extensions.blender.org/add-ons/cartesian-caramel-everyday-nodes/) | The geometry node groups I use in my everyday workflow | extensions.blender.org | CC0-1.0 |  | id в Blender: cartesian_caramel_everyday_nodes, проверена версия 1.0.0 |

### Дополнения Blender: 67

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [Sprite Sheet Maker](https://extensions.blender.org/add-ons/sprite-sheet-maker/) | 3D to 2D sprite sheet converter with optional pixelation | extensions.blender.org | GPL-3.0-or-later | 7.9 | id в Blender: sprite_sheet_maker, проверена версия 5.3.1 |
| [Bagapie](https://extensions.blender.org/add-ons/bagapie/) | 50+ tools : Scattering, Ivy Gen, Random Array, Architecture | extensions.blender.org | GPL-3.0-or-later | 12.6 | id в Blender: Bagapie, проверена версия 11.0.12 |
| [Moveset Free](https://extensions.blender.org/add-ons/moveset/) | 55 free procedural animations for any humanoid rig | extensions.blender.org | GPL-3.0-or-later | 10.0 | id в Blender: moveset, проверена версия 1.3.11 |
| [The Better Baker - PBR Baker](https://extensions.blender.org/add-ons/thebetterbaker/) | A PBR baker for multiple objects and complex materials | extensions.blender.org | GPL-3.0-or-later | 0.1 | id в Blender: thebetterbaker, проверена версия 5.1.1 |
| [Extra Mesh Objects](https://extensions.blender.org/add-ons/extra-mesh-objects/) | Add extra mesh object types | extensions.blender.org | GPL-3.0-or-later | 1.1 | id в Blender: extra_mesh_objects, проверена версия 0.4.1 |
| [Sapling Tree Gen](https://extensions.blender.org/add-ons/sapling-tree-gen/) | Adds a parametric tree with leaves, armature and wind | extensions.blender.org | GPL-3.0-or-later | 1.1 | id в Blender: sapling_tree_gen, проверена версия 1.2.0 |
| [A.N.T.Landscape](https://extensions.blender.org/add-ons/antlandscape/) | Another Noise Tool: Landscape and Displace | extensions.blender.org | GPL-2.0-or-later | 0.4 | id в Blender: antlandscape, проверена версия 0.2.0 |
| [Zeeks Auto UV Unwrap](https://extensions.blender.org/add-ons/zeeks-auto-uv-unwrap/) | Auto UV unwrap, Anti-Stretch Seams & Seam Picker | extensions.blender.org | GPL-3.0-or-later | 0.2 | id в Blender: zeeks_auto_uv_unwrap, проверена версия 2.0.0 |
| [UVgami Lite](https://extensions.blender.org/add-ons/uvgami/) | Automatic UV unwrapping | extensions.blender.org | GPL-3.0-or-later | 111.1 | id в Blender: uvgami, проверена версия 2.3.0 |
| [Vertex Animation Toolkit (VAT + VAB)](https://extensions.blender.org/add-ons/vat/) | Bake mesh animation to Vertex Animation Textures or Buffers | extensions.blender.org | GPL-3.0-or-later | 0.1 | id в Blender: VAT, проверена версия 1.0.12 |
| [VDM Brush Baker](https://extensions.blender.org/add-ons/vdm-brush-baker/) | Bake vector displacement brushes easily from a plane | extensions.blender.org | GPL-3.0-or-later |  | id в Blender: vdm_brush_baker, проверена версия 1.0.6 |
| [Brushstroke Tools](https://extensions.blender.org/add-ons/brushstroke-tools/) | Brushstroke painting tools by the Blender Studio | extensions.blender.org | GPL-3.0-or-later | 30.7 | id в Blender: brushstroke_tools, проверена версия 1.2.3 |
| [Mio3 Copy Weight](https://extensions.blender.org/add-ons/mio3-copy-weight/) | Copies weights of selected vertices across objects | extensions.blender.org | GPL-3.0-or-later | 0.1 | id в Blender: mio3_copy_weight, проверена версия 1.1.0 |
| [Copy Attributes Menu](https://extensions.blender.org/add-ons/copy-attributes-menu/) | Copy Attributes Menu | extensions.blender.org | GPL-3.0-or-later | 0.1 | id в Blender: copy_attributes_menu, проверена версия 0.6.3 |
| [Keymesh](https://extensions.blender.org/add-ons/keymesh/) | Create stop-motion animations by sculpting frame-by-frame | extensions.blender.org | GPL-3.0-or-later | 0.3 | id в Blender: keymesh, проверена версия 2.3.2 |
| [Scatter Objects](https://extensions.blender.org/add-ons/scatter-objects/) | Distribute object instances on another object | extensions.blender.org | GPL-2.0-or-later | 0.1 | id в Blender: scatter_objects, проверена версия 0.2.0 |
| [Devil Designer](https://extensions.blender.org/add-ons/devil-designer/) | Draft, sew, and drape clothing patterns inside Blender | extensions.blender.org | GPL-3.0-or-later | 2.5 | id в Blender: devil_designer, проверена версия 0.15.0 |
| [GamiFlow](https://extensions.blender.org/add-ons/gamiflow/) | Easier game asset creation | extensions.blender.org | GPL-3.0-or-later | 1.2 | id в Blender: gamiflow, проверена версия 1.10.1 |
| [Bone Widget](https://extensions.blender.org/add-ons/bone-widget/) | Easily Create Bone Widgets | extensions.blender.org | GPL-3.0-or-later | 1.1 | id в Blender: bone_widget, проверена версия 2.4.0 |
| [Editable Motion Paths](https://extensions.blender.org/add-ons/editable-motion-paths/) | Edit animation like a mesh, right on the motion path | extensions.blender.org | GPL-3.0-or-later | 3.9 | id в Blender: editable_motion_paths, проверена версия 2.0.8 |
| [Spine IO](https://extensions.blender.org/add-ons/spine-io/) | Export bone-driven Spine 4.3 JSON files | extensions.blender.org | GPL-3.0-or-later | 0.2 | id в Blender: spine_io, проверена версия 0.0.3 |
| [F2](https://extensions.blender.org/add-ons/f2/) | Extends the 'Make Edge/Face' functionality | extensions.blender.org | GPL-3.0-or-later |  | id в Blender: f2, проверена версия 1.8.5 |
| [Grease Pencil Tools](https://extensions.blender.org/add-ons/grease-pencil-tools/) | Extra tools for Grease Pencil | extensions.blender.org | GPL-3.0-or-later | 0.3 | id в Blender: grease_pencil_tools, проверена версия 2.3.1 |
| [Bake Preflight](https://extensions.blender.org/add-ons/bake-preflight/) | Find common texture baking mistakes before you bake | extensions.blender.org | GPL-3.0-or-later | 0.1 | id в Blender: bake_preflight, проверена версия 0.1.0 |
| [Cell Fracture](https://extensions.blender.org/add-ons/cell-fracture/) | Fractured Object Creation | extensions.blender.org | GPL-3.0-or-later | 0.1 | id в Blender: cell_fracture, проверена версия 0.2.1 |
| [LODGen](https://extensions.blender.org/add-ons/lod-gen/) | Generate LODs for Games in 3 Clicks or Less | extensions.blender.org | GPL-3.0-or-later | 0.1 | id в Blender: lod_gen, проверена версия 0.0.5 |
| [Mixamo Rig](https://extensions.blender.org/add-ons/mixamo-rig/) | Generate a control rig from Mixamo Fbx skeleton | extensions.blender.org | GPL-3.0-or-later | 1.4 | id в Blender: mixamo_rig, проверена версия 1.2.3 |
| [Hair Bone Generator](https://extensions.blender.org/add-ons/hair-bone-generator/) | Generate a deform bone chain along the run of a hair strand | extensions.blender.org | GPL-3.0-or-later | 0.7 | id в Blender: hair_bone_generator, проверена версия 1.2.0 |
| [EdgeFlow](https://extensions.blender.org/add-ons/edgeflow/) | Helps adjusting mesh geometry to curved surfaces | extensions.blender.org | GPL-3.0-or-later | 0.2 | id в Blender: EdgeFlow, проверена версия 1.1.2 |
| [Auto Wrinkle Map](https://extensions.blender.org/add-ons/auto-wrinkle-map/) | Helps you to create wrinkle maps driven from bones in one click | extensions.blender.org | GPL-3.0-or-later | 0.1 | id в Blender: auto_wrinkle_map, проверена версия 0.0.7 |
| [MPFB](https://extensions.blender.org/add-ons/mpfb/) | Human character generator and editor | extensions.blender.org | GPL-3.0-or-later | 79.8 | id в Blender: mpfb, проверена версия 2.0.18 |
| [Plume ALFATORA Bronze](https://extensions.blender.org/add-ons/plume-alfatora/) | Illustrator-style pen, chains, chain mail and ropes | extensions.blender.org | GPL-3.0-or-later | 1.1 | id в Blender: plume_alfatora, проверена версия 3.41.4 |
| [Frame By Plane](https://extensions.blender.org/add-ons/frame-by-plane/) | Image sequences, Grease Pencil and 2.5D animation | extensions.blender.org | GPL-3.0-or-later | 33.5 | id в Blender: frame_by_plane, проверена версия 8.5.1 |
| [Import .PSD as Mesh Planes](https://extensions.blender.org/add-ons/import-psd-as-mesh-planes/) | Imports Adobe Photoshop .PSD files into mesh planes | extensions.blender.org | GPL-3.0-or-later | 15.8 | id в Blender: import_psd_as_mesh_planes, проверена версия 2.6.3 |
| [Isometric Scene Setup](https://extensions.blender.org/add-ons/isometric-scene-setup/) | Isometric scene setup and 2D normal map rendering | extensions.blender.org | GPL-3.0-or-later,MIT |  | id в Blender: isometric_scene_setup, проверена версия 1.0.1 |
| [Ucupaint](https://extensions.blender.org/add-ons/ucupaint/) | Layer based painting for Eevee and Cycles | extensions.blender.org | GPL-3.0-or-later | 15.1 | id в Blender: ucupaint, проверена версия 3.0.2 |
| [LookDeck](https://extensions.blender.org/add-ons/pbr-lookdev/) | Layered PBR lookdev with smart masks and a lookdev kit | extensions.blender.org | GPL-3.0-or-later | 0.6 | id в Blender: pbr_lookdev, проверена версия 5.0.0 |
| [Sculptools: Layers](https://extensions.blender.org/add-ons/sculptools-layers/) | Layers system for non-destructive sculpting workflow | extensions.blender.org | GPL-3.0-or-later | 0.4 | id в Blender: sculptools_layers, проверена версия 1.1.0 |
| [Web3D Asset Compiler](https://extensions.blender.org/add-ons/web3d-asset-compiler/) | Lightmap baking, mesh optimization, and Three.js export | extensions.blender.org | GPL-3.0-or-later | 0.8 | id в Blender: web3d_asset_compiler, проверена версия 1.1.0 |
| [Material Utilities](https://extensions.blender.org/add-ons/material-utilities/) | Menu of material tools (assign, select..) in the 3D View | extensions.blender.org | GPL-3.0-or-later | 0.2 | id в Blender: material_utilities, проверена версия 2.2.3 |
| [LoopTools](https://extensions.blender.org/add-ons/looptools/) | Mesh modelling toolkit. Several tools to aid modelling | extensions.blender.org | GPL-2.0-or-later | 0.4 | id в Blender: looptools, проверена версия 4.7.7 |
| [Bsurfaces GPL Edition](https://extensions.blender.org/add-ons/bsurfaces-gpl-edition/) | Modeling and retopology tool | extensions.blender.org | GPL-3.0-or-later | 0.4 | id в Blender: bsurfaces_gpl_edition, проверена версия 1.8.4 |
| [Bulletproof Retarget](https://extensions.blender.org/add-ons/bulletproof-retarget/) | One-click animation retargeting: P2M, Mixamo, Rigify and more | extensions.blender.org | GPL-3.0-or-later | 0.6 | id в Blender: bulletproof_retarget, проверена версия 1.3.5 |
| [AmbientCG Material Importer](https://extensions.blender.org/add-ons/ambientcg-material-importer/) | One-click material creation from AmbientCG | extensions.blender.org | GPL-3.0-or-later |  | id в Blender: ambientcg_material_importer, проверена версия 1.5.0 |
| [B Onion Skin](https://extensions.blender.org/add-ons/b-onion-skin/) | Onion skinning for 3D animation | extensions.blender.org | GPL-3.0-or-later | 0.1 | id в Blender: b_onion_skin, проверена версия 1.1.0 |
| [Hardflow](https://extensions.blender.org/add-ons/hardflow/) | Open source hard surface boolean modeling toolkit | extensions.blender.org | GPL-3.0-or-later | 1.8 | id в Blender: hardflow, проверена версия 1.22.0 |
| [Half Knife](https://extensions.blender.org/add-ons/half-knife/) | Optimized for fast workflow knife tool for Blender | extensions.blender.org | GPL-3.0-or-later | 0.1 | id в Blender: Half_Knife, проверена версия 1.3.85 |
| [Pose Shape Keys](https://extensions.blender.org/add-ons/pose-shape-keys/) | Preserve your shape keys through weight changes, and much more | extensions.blender.org | GPL-3.0-or-later | 0.2 | id в Blender: pose_shape_keys, проверена версия 1.1.1 |
| [Dynamic Sky](https://extensions.blender.org/add-ons/dynamic-sky/) | Procedural sky for Cycles and Eevee: presets, HDRI, night mode | extensions.blender.org | GPL-3.0-or-later | 0.4 | id в Blender: dynamic_sky, проверена версия 1.1.0 |
| [CurioMesh](https://extensions.blender.org/add-ons/curiomesh/) | Quad retopology for scans and game assets | extensions.blender.org | GPL-3.0-or-later | 11.2 | id в Blender: curiomesh, проверена версия 0.9.9 |
| [Bool Tool](https://extensions.blender.org/add-ons/bool-tool/) | Quick Boolean operators and tools for hard surface modeling | extensions.blender.org | GPL-3.0-or-later | 0.6 | id в Blender: bool_tool, проверена версия 2.1.0 |
| [GP Tween (c)](https://extensions.blender.org/add-ons/gp-tween/) | Quick Grease Pencil Tweening | extensions.blender.org | GPL-3.0-or-later | 1.7 | id в Blender: gp_tween, проверена версия 2.4.0 |
| [Wiggle Bones](https://extensions.blender.org/add-ons/wiggle-bones/) | Refactor of Wiggle 2, fully fixed for Blender 5.0 | extensions.blender.org | GPL-3.0-or-later | 0.2 | id в Blender: wiggle_bones, проверена версия 1.1.2 |
| [PolyQuilt Retopology Tool](https://extensions.blender.org/add-ons/polyquilt-fork/) | Retopology Tool for Blender | extensions.blender.org | GPL-3.0-or-later | 1.3 | id в Blender: PolyQuilt_Fork, проверена версия 1.46.8 |
| [CloudRig](https://extensions.blender.org/add-ons/cloudrig/) | Rig Generation & Rigging Workflow Tools | extensions.blender.org | GPL-3.0-or-later | 4.7 | id в Blender: cloudrig, проверена версия 2.2.32 |
| [Storytools - Storyboard Tools](https://extensions.blender.org/add-ons/storytools/) | Set of tools for Storyboarding and 2D animation | extensions.blender.org | GPL-3.0-or-later | 1.9 | id в Blender: storytools, проверена версия 4.0.0 |
| [ClothDrop Reborn](https://extensions.blender.org/add-ons/clothdrop-reborn/) | Single-click cloth simulation tool | extensions.blender.org | GPL-3.0-or-later | 0.1 | id в Blender: clothdrop_reborn, проверена версия 2.0.3 |
| [EasyMesh Batch Exporter](https://extensions.blender.org/add-ons/easymesh-batch-exporter/) | Streamlined mesh export for game development workflows | extensions.blender.org | GPL-3.0-or-later | 0.6 | id в Blender: easymesh_batch_exporter, проверена версия 1.6.2 |
| [Unravel](https://extensions.blender.org/add-ons/unravel/) | Tear holes in cloth and grow frayed threads around them | extensions.blender.org | GPL-3.0-or-later | 2.4 | id в Blender: unravel, проверена версия 1.1.0 |
| [PAWS: Bakery](https://extensions.blender.org/add-ons/paws-bakery/) | Texture Baking tools for Game-Ready pipeline by Pawsgineer | extensions.blender.org | GPL-3.0-or-later | 1.1 | id в Blender: paws_bakery, проверена версия 0.5.1 |
| [Tissue](https://extensions.blender.org/add-ons/tissue/) | Tools for Computational Design | extensions.blender.org | GPL-3.0-or-later | 1.4 | id в Blender: tissue, проверена версия 0.3.76 |
| [Sequenced Bake](https://extensions.blender.org/add-ons/sequenced-bake/) | Tools for baking material sequences and generating sprite sheets | extensions.blender.org | GPL-3.0-or-later | 0.9 | id в Blender: sequenced_bake, проверена версия 1.2.1 |
| [BTracer](https://extensions.blender.org/add-ons/btracer/) | Tools for converting/animating objects/particles into curves | extensions.blender.org | GPL-2.0-or-later | 0.2 | id в Blender: btracer, проверена версия 1.2.4 |
| [Texel Density Checker](https://extensions.blender.org/add-ons/texel-density-checker/) | Toolset for working with Texel Density | extensions.blender.org | GPL-3.0-or-later | 0.2 | id в Blender: texel_density_checker, проверена версия 2026.1.1 |
| [MeshDataTransfer](https://extensions.blender.org/add-ons/mesh-data-transfer/) | Transfer mesh data and attributes between objects | extensions.blender.org | GPL-3.0-or-later | 0.2 | id в Blender: mesh_data_transfer, проверена версия 2.1.0 |
| [PropGon UV Trim](https://extensions.blender.org/add-ons/propgon-uv-trim/) | UV Trimsheet tools for layout, fitting and texel density | extensions.blender.org | GPL-3.0-or-later | 0.5 | id в Blender: propgon_uv_trim, проверена версия 2.1.3 |
| [EasyWeight](https://extensions.blender.org/add-ons/easyweight/) | Weight Painting Workflow Boosters | extensions.blender.org | GPL-3.0-or-later | 0.3 | id в Blender: easyweight, проверена версия 1.1.3 |

### Персонажи и одежда: 48

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [arms01](https://static.makehumancommunity.org/assets/assetpacks/arms01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 0.2 | у части вещей внутри другая лицензия, см. avoid |
| [bodyparts01](https://static.makehumancommunity.org/assets/assetpacks/bodyparts01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 0.8 | у части вещей внутри другая лицензия, см. avoid |
| [bodyparts02](https://static.makehumancommunity.org/assets/assetpacks/bodyparts02.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 10.8 | у части вещей внутри другая лицензия, см. avoid |
| [bodyparts03](https://static.makehumancommunity.org/assets/assetpacks/bodyparts03.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 38.8 | у части вещей внутри другая лицензия, см. avoid |
| [bodyparts05](https://static.makehumancommunity.org/assets/assetpacks/bodyparts05.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 6.6 | у части вещей внутри другая лицензия, см. avoid |
| [bodyparts06](https://static.makehumancommunity.org/assets/assetpacks/bodyparts06.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 13.0 | у части вещей внутри другая лицензия, см. avoid |
| [cheek01](https://static.makehumancommunity.org/assets/assetpacks/cheek01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 0.4 | у части вещей внутри другая лицензия, см. avoid |
| [ears01](https://static.makehumancommunity.org/assets/assetpacks/ears01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 0.6 | у части вещей внутри другая лицензия, см. avoid |
| [equipment01](https://static.makehumancommunity.org/assets/assetpacks/equipment01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 18.1 | у части вещей внутри другая лицензия, см. avoid |
| [equipment02](https://static.makehumancommunity.org/assets/assetpacks/equipment02.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 13.4 | у части вещей внутри другая лицензия, см. avoid |
| [equipment03](https://static.makehumancommunity.org/assets/assetpacks/equipment03.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 128.1 | у части вещей внутри другая лицензия, см. avoid |
| [eyebrows01](https://static.makehumancommunity.org/assets/assetpacks/eyebrows01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 11.5 | у части вещей внутри другая лицензия, см. avoid |
| [eyelashes01](https://static.makehumancommunity.org/assets/assetpacks/eyelashes01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 3.5 | у части вещей внутри другая лицензия, см. avoid |
| [faceunits01](https://static.makehumancommunity.org/assets/assetpacks/faceunits01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 0.3 | у части вещей внутри другая лицензия, см. avoid |
| [gloves01](https://static.makehumancommunity.org/assets/assetpacks/gloves01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 3.2 | у части вещей внутри другая лицензия, см. avoid |
| [hair01](https://static.makehumancommunity.org/assets/assetpacks/hair01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 227.8 | у части вещей внутри другая лицензия, см. avoid |
| [hair02](https://static.makehumancommunity.org/assets/assetpacks/hair02.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 72.3 | у части вещей внутри другая лицензия, см. avoid |
| [hair03](https://static.makehumancommunity.org/assets/assetpacks/hair03.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 40.1 | у части вещей внутри другая лицензия, см. avoid |
| [haireditor](https://static.makehumancommunity.org/assets/assetpacks/haireditor.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 18.3 | у части вещей внутри другая лицензия, см. avoid |
| [hands01](https://static.makehumancommunity.org/assets/assetpacks/hands01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 0.2 | у части вещей внутри другая лицензия, см. avoid |
| [hats01](https://static.makehumancommunity.org/assets/assetpacks/hats01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 6.6 | у части вещей внутри другая лицензия, см. avoid |
| [hats02](https://static.makehumancommunity.org/assets/assetpacks/hats02.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 24.0 | у части вещей внутри другая лицензия, см. avoid |
| [hats03](https://static.makehumancommunity.org/assets/assetpacks/hats03.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 76.0 | у части вещей внутри другая лицензия, см. avoid |
| [hats04](https://static.makehumancommunity.org/assets/assetpacks/hats04.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 17.9 | у части вещей внутри другая лицензия, см. avoid |
| [makehuman_system_assets](https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 280.7 | у части вещей внутри другая лицензия, см. avoid |
| [masks01](https://static.makehumancommunity.org/assets/assetpacks/masks01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 4.3 | у части вещей внутри другая лицензия, см. avoid |
| [masks02](https://static.makehumancommunity.org/assets/assetpacks/masks02.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 18.1 | у части вещей внутри другая лицензия, см. avoid |
| [nose01](https://static.makehumancommunity.org/assets/assetpacks/nose01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 1.3 | у части вещей внутри другая лицензия, см. avoid |
| [pants01](https://static.makehumancommunity.org/assets/assetpacks/pants01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 21.9 | у части вещей внутри другая лицензия, см. avoid |
| [pants02](https://static.makehumancommunity.org/assets/assetpacks/pants02.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 131.8 | у части вещей внутри другая лицензия, см. avoid |
| [poses02](https://static.makehumancommunity.org/assets/assetpacks/poses02.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 1.6 | у части вещей внутри другая лицензия, см. avoid |
| [shirts01](https://static.makehumancommunity.org/assets/assetpacks/shirts01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 24.5 | у части вещей внутри другая лицензия, см. avoid |
| [shirts02](https://static.makehumancommunity.org/assets/assetpacks/shirts02.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 175.4 | у части вещей внутри другая лицензия, см. avoid |
| [shirts03](https://static.makehumancommunity.org/assets/assetpacks/shirts03.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 71.7 | у части вещей внутри другая лицензия, см. avoid |
| [shoes01](https://static.makehumancommunity.org/assets/assetpacks/shoes01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 83.0 | у части вещей внутри другая лицензия, см. avoid |
| [shoes03](https://static.makehumancommunity.org/assets/assetpacks/shoes03.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 50.3 | у части вещей внутри другая лицензия, см. avoid |
| [skins01](https://static.makehumancommunity.org/assets/assetpacks/skins01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 104.2 | у части вещей внутри другая лицензия, см. avoid |
| [skins02](https://static.makehumancommunity.org/assets/assetpacks/skins02.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 76.1 | у части вещей внутри другая лицензия, см. avoid |
| [skins03](https://static.makehumancommunity.org/assets/assetpacks/skins03.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 136.8 | у части вещей внутри другая лицензия, см. avoid |
| [skirts01](https://static.makehumancommunity.org/assets/assetpacks/skirts01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 29.6 | у части вещей внутри другая лицензия, см. avoid |
| [suits01](https://static.makehumancommunity.org/assets/assetpacks/suits01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 42.6 | у части вещей внутри другая лицензия, см. avoid |
| [suits02](https://static.makehumancommunity.org/assets/assetpacks/suits02.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 192.5 | у части вещей внутри другая лицензия, см. avoid |
| [suits03](https://static.makehumancommunity.org/assets/assetpacks/suits03.html) | mpfb pack | MakeHuman Community | CC BY 4.0 | 105.3 | у части вещей внутри другая лицензия, см. avoid |
| [system_clothes_materials01](https://static.makehumancommunity.org/assets/assetpacks/system_clothes_materials01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 48.2 | у части вещей внутри другая лицензия, см. avoid |
| [system_hair_materials01](https://static.makehumancommunity.org/assets/assetpacks/system_hair_materials01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 86.8 | у части вещей внутри другая лицензия, см. avoid |
| [underwear04](https://static.makehumancommunity.org/assets/assetpacks/underwear04.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 5.6 | у части вещей внутри другая лицензия, см. avoid |
| [visemes01](https://static.makehumancommunity.org/assets/assetpacks/visemes01.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 0.2 | у части вещей внутри другая лицензия, см. avoid |
| [visemes02](https://static.makehumancommunity.org/assets/assetpacks/visemes02.html) | mpfb pack | MakeHuman Community | CC0 1.0 | 0.1 | у части вещей внутри другая лицензия, см. avoid |

### Анимации: 2

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [Universal Animation Library](https://opengameart.org/content/universal-animation-library) | universal-animation-library | OpenGameArt | CC0 1.0 | 14.5 |  |
| [Universal Animation Library 2](https://opengameart.org/content/universal-animation-library-2) | universal-animation-library-2 | OpenGameArt | CC0 1.0 | 10.3 |  |

### Материалы: 285

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [bark_brown_02](https://polyhaven.com/a/bark_brown_02) | scan | Poly Haven | CC0 1.0 | 33.4 |  |
| [beam_wall_01](https://polyhaven.com/a/beam_wall_01) | scan | Poly Haven | CC0 1.0 | 9.2 |  |
| [brown_leather](https://polyhaven.com/a/brown_leather) | scan | Poly Haven | CC0 1.0 | 34.6 |  |
| [brown_mud_03](https://polyhaven.com/a/brown_mud_03) | scan | Poly Haven | CC0 1.0 | 30.1 |  |
| [brown_planks_09](https://polyhaven.com/a/brown_planks_09) | scan | Poly Haven | CC0 1.0 | 28.3 |  |
| [caban](https://polyhaven.com/a/caban) | scan | Poly Haven | CC0 1.0 | 57.0 |  |
| [castle_brick_01](https://polyhaven.com/a/castle_brick_01) | scan | Poly Haven | CC0 1.0 | 39.4 |  |
| [castle_wall_slates](https://polyhaven.com/a/castle_wall_slates) | scan | Poly Haven | CC0 1.0 | 40.4 |  |
| [castle_wall_varriation](https://polyhaven.com/a/castle_wall_varriation) | scan | Poly Haven | CC0 1.0 | 35.7 |  |
| [cliff_side](https://polyhaven.com/a/cliff_side) | scan | Poly Haven | CC0 1.0 | 38.3 |  |
| [coast_sand_01](https://polyhaven.com/a/coast_sand_01) | scan | Poly Haven | CC0 1.0 | 46.3 |  |
| [cobblestone_floor_08](https://polyhaven.com/a/cobblestone_floor_08) | scan | Poly Haven | CC0 1.0 | 34.6 |  |
| [coral_fort_wall_01](https://polyhaven.com/a/coral_fort_wall_01) | scan | Poly Haven | CC0 1.0 | 60.3 |  |
| [crepe_satin](https://polyhaven.com/a/crepe_satin) | scan | Poly Haven | CC0 1.0 | 83.3 |  |
| [curly_teddy_natural](https://polyhaven.com/a/curly_teddy_natural) | scan | Poly Haven | CC0 1.0 | 36.9 |  |
| [damp_beach_sand_02](https://polyhaven.com/a/damp_beach_sand_02) | scan | Poly Haven | CC0 1.0 | 56.3 |  |
| [damp_sand](https://polyhaven.com/a/damp_sand) | scan | Poly Haven | CC0 1.0 | 62.9 |  |
| [dark_planks](https://polyhaven.com/a/dark_planks) | scan | Poly Haven | CC0 1.0 | 27.0 |  |
| [dark_rock_02](https://polyhaven.com/a/dark_rock_02) | scan | Poly Haven | CC0 1.0 | 41.8 |  |
| [dark_wood](https://polyhaven.com/a/dark_wood) | scan | Poly Haven | CC0 1.0 | 42.1 |  |
| [dark_wooden_planks](https://polyhaven.com/a/dark_wooden_planks) | scan | Poly Haven | CC0 1.0 | 41.2 |  |
| [defense_wall](https://polyhaven.com/a/defense_wall) | scan | Poly Haven | CC0 1.0 | 30.4 |  |
| [dense_sand](https://polyhaven.com/a/dense_sand) | scan | Poly Haven | CC0 1.0 | 45.6 |  |
| [fabric_leather_01](https://polyhaven.com/a/fabric_leather_01) | scan | Poly Haven | CC0 1.0 | 41.2 |  |
| [fabric_leather_02](https://polyhaven.com/a/fabric_leather_02) | scan | Poly Haven | CC0 1.0 | 33.3 |  |
| [faux_fur_geometric](https://polyhaven.com/a/faux_fur_geometric) | scan | Poly Haven | CC0 1.0 | 53.0 |  |
| [floral_jacquard](https://polyhaven.com/a/floral_jacquard) | scan | Poly Haven | CC0 1.0 | 125.7 |  |
| [green_metal_rust](https://polyhaven.com/a/green_metal_rust) | scan | Poly Haven | CC0 1.0 | 20.1 |  |
| [hessian_230](https://polyhaven.com/a/hessian_230) | scan | Poly Haven | CC0 1.0 | 65.4 |  |
| [hessian_380](https://polyhaven.com/a/hessian_380) | scan | Poly Haven | CC0 1.0 | 67.2 |  |
| [knitted_fleece](https://polyhaven.com/a/knitted_fleece) | scan | Poly Haven | CC0 1.0 | 82.4 |  |
| [leather_red_02](https://polyhaven.com/a/leather_red_02) | scan | Poly Haven | CC0 1.0 | 42.8 |  |
| [leather_red_03](https://polyhaven.com/a/leather_red_03) | scan | Poly Haven | CC0 1.0 | 36.5 |  |
| [leather_white](https://polyhaven.com/a/leather_white) | scan | Poly Haven | CC0 1.0 | 60.0 |  |
| [lichen_rock](https://polyhaven.com/a/lichen_rock) | scan | Poly Haven | CC0 1.0 | 51.3 |  |
| [marble_cliff_01](https://polyhaven.com/a/marble_cliff_01) | scan | Poly Haven | CC0 1.0 | 32.9 |  |
| [medieval_blocks_02](https://polyhaven.com/a/medieval_blocks_02) | scan | Poly Haven | CC0 1.0 | 34.8 |  |
| [medieval_blocks_05](https://polyhaven.com/a/medieval_blocks_05) | scan | Poly Haven | CC0 1.0 | 32.8 |  |
| [medieval_blocks_06](https://polyhaven.com/a/medieval_blocks_06) | scan | Poly Haven | CC0 1.0 | 34.9 |  |
| [medieval_wall_02](https://polyhaven.com/a/medieval_wall_02) | scan | Poly Haven | CC0 1.0 | 51.4 |  |
| [medieval_wood](https://polyhaven.com/a/medieval_wood) | scan | Poly Haven | CC0 1.0 | 32.8 |  |
| [metal_grate_rusty](https://polyhaven.com/a/metal_grate_rusty) | scan | Poly Haven | CC0 1.0 | 56.5 |  |
| [metal_plate](https://polyhaven.com/a/metal_plate) | scan | Poly Haven | CC0 1.0 | 55.7 |  |
| [metal_plate_02](https://polyhaven.com/a/metal_plate_02) | scan | Poly Haven | CC0 1.0 | 39.8 |  |
| [monastery_stone_floor](https://polyhaven.com/a/monastery_stone_floor) | scan | Poly Haven | CC0 1.0 | 44.4 |  |
| [moss_wood](https://polyhaven.com/a/moss_wood) | scan | Poly Haven | CC0 1.0 | 35.0 |  |
| [mossy_rock](https://polyhaven.com/a/mossy_rock) | scan | Poly Haven | CC0 1.0 | 57.6 |  |
| [old_planks_02](https://polyhaven.com/a/old_planks_02) | scan | Poly Haven | CC0 1.0 | 25.7 |  |
| [old_wood_floor](https://polyhaven.com/a/old_wood_floor) | scan | Poly Haven | CC0 1.0 | 44.0 |  |
| [poly_wool_herringbone](https://polyhaven.com/a/poly_wool_herringbone) | scan | Poly Haven | CC0 1.0 | 77.9 |  |
| [quatrefoil_jacquard_fabric](https://polyhaven.com/a/quatrefoil_jacquard_fabric) | scan | Poly Haven | CC0 1.0 | 64.4 |  |
| [rabdentse_ruins_wall](https://polyhaven.com/a/rabdentse_ruins_wall) | scan | Poly Haven | CC0 1.0 | 56.2 |  |
| [red_sand](https://polyhaven.com/a/red_sand) | scan | Poly Haven | CC0 1.0 | 52.3 |  |
| [ribbed_corduroy](https://polyhaven.com/a/ribbed_corduroy) | scan | Poly Haven | CC0 1.0 | 73.7 |  |
| [rock_face_03](https://polyhaven.com/a/rock_face_03) | scan | Poly Haven | CC0 1.0 | 54.0 |  |
| [rough_linen](https://polyhaven.com/a/rough_linen) | scan | Poly Haven | CC0 1.0 | 71.5 |  |
| [rust_coarse_01](https://polyhaven.com/a/rust_coarse_01) | scan | Poly Haven | CC0 1.0 | 56.7 |  |
| [rusty_metal](https://polyhaven.com/a/rusty_metal) | scan | Poly Haven | CC0 1.0 | 27.1 |  |
| [rusty_metal_02](https://polyhaven.com/a/rusty_metal_02) | scan | Poly Haven | CC0 1.0 | 24.1 |  |
| [rusty_metal_03](https://polyhaven.com/a/rusty_metal_03) | scan | Poly Haven | CC0 1.0 | 40.9 |  |
| [rusty_metal_04](https://polyhaven.com/a/rusty_metal_04) | scan | Poly Haven | CC0 1.0 | 53.5 |  |
| [rusty_metal_05](https://polyhaven.com/a/rusty_metal_05) | scan | Poly Haven | CC0 1.0 | 35.3 |  |
| [rusty_metal_sheet](https://polyhaven.com/a/rusty_metal_sheet) | scan | Poly Haven | CC0 1.0 | 37.8 |  |
| [sand_03](https://polyhaven.com/a/sand_03) | scan | Poly Haven | CC0 1.0 | 49.8 |  |
| [scuba_suede](https://polyhaven.com/a/scuba_suede) | scan | Poly Haven | CC0 1.0 | 86.3 |  |
| [velour_velvet](https://polyhaven.com/a/velour_velvet) | scan | Poly Haven | CC0 1.0 | 60.4 |  |
| [wool_boucle](https://polyhaven.com/a/wool_boucle) | scan | Poly Haven | CC0 1.0 | 84.4 |  |
| [Bark014](https://ambientcg.com/a/Bark014) | Bark | ambientCG | CC0 1.0 | 29.8 |  |
| [Bark016](https://ambientcg.com/a/Bark016) | Bark | ambientCG | CC0 1.0 | 30.2 |  |
| [Bricks105](https://ambientcg.com/a/Bricks105) | Bricks | ambientCG | CC0 1.0 | 14.9 |  |
| [Bricks106A](https://ambientcg.com/a/Bricks106A) | Bricks | ambientCG | CC0 1.0 | 27.7 |  |
| [Bricks108A](https://ambientcg.com/a/Bricks108A) | Bricks | ambientCG | CC0 1.0 | 26.6 |  |
| [Bricks109A](https://ambientcg.com/a/Bricks109A) | Bricks | ambientCG | CC0 1.0 | 27.1 |  |
| [Bricks112A](https://ambientcg.com/a/Bricks112A) | Bricks | ambientCG | CC0 1.0 | 26.8 |  |
| [Bricks113A](https://ambientcg.com/a/Bricks113A) | Bricks | ambientCG | CC0 1.0 | 26.5 |  |
| [Carpet001](https://ambientcg.com/a/Carpet001) | Carpet | ambientCG | CC0 1.0 | 29.6 |  |
| [Carpet012](https://ambientcg.com/a/Carpet012) | Carpet | ambientCG | CC0 1.0 | 36.6 |  |
| [Carpet016](https://ambientcg.com/a/Carpet016) | Carpet | ambientCG | CC0 1.0 | 31.2 |  |
| [Chainmail001](https://ambientcg.com/a/Chainmail001) | Chainmail | ambientCG | CC0 1.0 | 167.7 |  |
| [Chainmail002](https://ambientcg.com/a/Chainmail002) | Chainmail | ambientCG | CC0 1.0 | 165.9 |  |
| [Chainmail003](https://ambientcg.com/a/Chainmail003) | Chainmail | ambientCG | CC0 1.0 | 157.8 |  |
| [Chainmail004](https://ambientcg.com/a/Chainmail004) | Chainmail | ambientCG | CC0 1.0 | 72.2 |  |
| [Fabric019](https://ambientcg.com/a/Fabric019) | Fabric | ambientCG | CC0 1.0 | 83.9 |  |
| [Fabric023](https://ambientcg.com/a/Fabric023) | Fabric | ambientCG | CC0 1.0 | 126.4 |  |
| [Fabric026](https://ambientcg.com/a/Fabric026) | Fabric | ambientCG | CC0 1.0 | 103.9 |  |
| [Fabric028](https://ambientcg.com/a/Fabric028) | Fabric | ambientCG | CC0 1.0 | 107.6 |  |
| [Fabric030](https://ambientcg.com/a/Fabric030) | Fabric | ambientCG | CC0 1.0 | 130.6 |  |
| [Fabric032](https://ambientcg.com/a/Fabric032) | Fabric | ambientCG | CC0 1.0 | 103.9 |  |
| [Fabric036](https://ambientcg.com/a/Fabric036) | Fabric | ambientCG | CC0 1.0 | 118.9 |  |
| [Fabric039](https://ambientcg.com/a/Fabric039) | Fabric | ambientCG | CC0 1.0 | 140.4 |  |
| [Fabric045](https://ambientcg.com/a/Fabric045) | Fabric | ambientCG | CC0 1.0 | 117.9 |  |
| [Fabric048](https://ambientcg.com/a/Fabric048) | Fabric | ambientCG | CC0 1.0 | 94.7 |  |
| [Fabric060](https://ambientcg.com/a/Fabric060) | Fabric | ambientCG | CC0 1.0 | 116.6 |  |
| [Fabric061](https://ambientcg.com/a/Fabric061) | Fabric | ambientCG | CC0 1.0 | 128.1 |  |
| [Fabric062](https://ambientcg.com/a/Fabric062) | Fabric | ambientCG | CC0 1.0 | 122.5 |  |
| [Fabric063](https://ambientcg.com/a/Fabric063) | Fabric | ambientCG | CC0 1.0 | 130.2 |  |
| [Fabric066](https://ambientcg.com/a/Fabric066) | Fabric | ambientCG | CC0 1.0 | 141.2 |  |
| [Fabric077](https://ambientcg.com/a/Fabric077) | Fabric | ambientCG | CC0 1.0 | 117.1 |  |
| [Fabric079](https://ambientcg.com/a/Fabric079) | Fabric | ambientCG | CC0 1.0 | 100.5 |  |
| [Fabric080](https://ambientcg.com/a/Fabric080) | Fabric | ambientCG | CC0 1.0 | 41.6 |  |
| [Fabric081A](https://ambientcg.com/a/Fabric081A) | Fabric | ambientCG | CC0 1.0 | 119.7 |  |
| [Fabric081B](https://ambientcg.com/a/Fabric081B) | Fabric | ambientCG | CC0 1.0 | 82.5 |  |
| [Fabric081C](https://ambientcg.com/a/Fabric081C) | Fabric | ambientCG | CC0 1.0 | 88.4 |  |
| [Fabric082A](https://ambientcg.com/a/Fabric082A) | Fabric | ambientCG | CC0 1.0 | 121.0 |  |
| [Fabric083](https://ambientcg.com/a/Fabric083) | Fabric | ambientCG | CC0 1.0 | 64.4 |  |
| [Fabric084](https://ambientcg.com/a/Fabric084) | Fabric | ambientCG | CC0 1.0 | 110.2 |  |
| [Fabric085](https://ambientcg.com/a/Fabric085) | Fabric | ambientCG | CC0 1.0 | 119.8 |  |
| [Fabric086](https://ambientcg.com/a/Fabric086) | Fabric | ambientCG | CC0 1.0 | 80.3 |  |
| [Fingerprints002](https://ambientcg.com/a/Fingerprints002) | Fingerprints | ambientCG | CC0 1.0 | 17.5 |  |
| [Fingerprints008](https://ambientcg.com/a/Fingerprints008) | Fingerprints | ambientCG | CC0 1.0 | 13.4 |  |
| [Fingerprints009](https://ambientcg.com/a/Fingerprints009) | Fingerprints | ambientCG | CC0 1.0 | 13.5 |  |
| [Foil002](https://ambientcg.com/a/Foil002) | Foil | ambientCG | CC0 1.0 | 22.8 |  |
| [Foil003](https://ambientcg.com/a/Foil003) | Foil | ambientCG | CC0 1.0 | 16.9 |  |
| [Ground103](https://ambientcg.com/a/Ground103) | Ground | ambientCG | CC0 1.0 | 33.8 |  |
| [Ground106](https://ambientcg.com/a/Ground106) | Ground | ambientCG | CC0 1.0 | 34.2 |  |
| [Ground107](https://ambientcg.com/a/Ground107) | Ground | ambientCG | CC0 1.0 | 34.7 |  |
| [Ground108](https://ambientcg.com/a/Ground108) | Ground | ambientCG | CC0 1.0 | 32.5 |  |
| [Ground109](https://ambientcg.com/a/Ground109) | Ground | ambientCG | CC0 1.0 | 31.8 |  |
| [Ground110](https://ambientcg.com/a/Ground110) | Ground | ambientCG | CC0 1.0 | 35.2 |  |
| [Ground111](https://ambientcg.com/a/Ground111) | Ground | ambientCG | CC0 1.0 | 34.4 |  |
| [Ground112](https://ambientcg.com/a/Ground112) | Ground | ambientCG | CC0 1.0 | 33.0 |  |
| [Ice002](https://ambientcg.com/a/Ice002) | Ice | ambientCG | CC0 1.0 | 19.8 |  |
| [Ice003](https://ambientcg.com/a/Ice003) | Ice | ambientCG | CC0 1.0 | 15.6 |  |
| [Ivory002A](https://ambientcg.com/a/Ivory002A) | Ivory | ambientCG | CC0 1.0 | 7.3 |  |
| [Ivory002B](https://ambientcg.com/a/Ivory002B) | Ivory | ambientCG | CC0 1.0 | 7.8 |  |
| [Lava001](https://ambientcg.com/a/Lava001) | Lava | ambientCG | CC0 1.0 | 34.5 |  |
| [Lava004](https://ambientcg.com/a/Lava004) | Lava | ambientCG | CC0 1.0 | 32.4 |  |
| [Leather008](https://ambientcg.com/a/Leather008) | Leather | ambientCG | CC0 1.0 | 104.7 |  |
| [Leather011](https://ambientcg.com/a/Leather011) | Leather | ambientCG | CC0 1.0 | 70.2 |  |
| [Leather012](https://ambientcg.com/a/Leather012) | Leather | ambientCG | CC0 1.0 | 74.1 |  |
| [Leather014](https://ambientcg.com/a/Leather014) | Leather | ambientCG | CC0 1.0 | 92.5 |  |
| [Leather023](https://ambientcg.com/a/Leather023) | Leather | ambientCG | CC0 1.0 | 91.6 |  |
| [Leather024](https://ambientcg.com/a/Leather024) | Leather | ambientCG | CC0 1.0 | 80.0 |  |
| [Leather025](https://ambientcg.com/a/Leather025) | Leather | ambientCG | CC0 1.0 | 74.6 |  |
| [Leather026](https://ambientcg.com/a/Leather026) | Leather | ambientCG | CC0 1.0 | 83.3 |  |
| [Leather027](https://ambientcg.com/a/Leather027) | Leather | ambientCG | CC0 1.0 | 79.4 |  |
| [Leather028](https://ambientcg.com/a/Leather028) | Leather | ambientCG | CC0 1.0 | 105.6 |  |
| [Leather029](https://ambientcg.com/a/Leather029) | Leather | ambientCG | CC0 1.0 | 105.1 |  |
| [Leather030](https://ambientcg.com/a/Leather030) | Leather | ambientCG | CC0 1.0 | 106.8 |  |
| [Leather031](https://ambientcg.com/a/Leather031) | Leather | ambientCG | CC0 1.0 | 94.6 |  |
| [Leather032](https://ambientcg.com/a/Leather032) | Leather | ambientCG | CC0 1.0 | 93.5 |  |
| [Leather033A](https://ambientcg.com/a/Leather033A) | Leather | ambientCG | CC0 1.0 | 95.5 |  |
| [Leather033B](https://ambientcg.com/a/Leather033B) | Leather | ambientCG | CC0 1.0 | 96.6 |  |
| [Leather033C](https://ambientcg.com/a/Leather033C) | Leather | ambientCG | CC0 1.0 | 109.2 |  |
| [Leather034C](https://ambientcg.com/a/Leather034C) | Leather | ambientCG | CC0 1.0 | 107.0 |  |
| [Leather034D](https://ambientcg.com/a/Leather034D) | Leather | ambientCG | CC0 1.0 | 106.1 |  |
| [Leather035D](https://ambientcg.com/a/Leather035D) | Leather | ambientCG | CC0 1.0 | 110.3 |  |
| [Leather036D](https://ambientcg.com/a/Leather036D) | Leather | ambientCG | CC0 1.0 | 117.3 |  |
| [Leather037](https://ambientcg.com/a/Leather037) | Leather | ambientCG | CC0 1.0 | 61.2 |  |
| [Leather038](https://ambientcg.com/a/Leather038) | Leather | ambientCG | CC0 1.0 | 100.2 |  |
| [Leather039](https://ambientcg.com/a/Leather039) | Leather | ambientCG | CC0 1.0 | 106.6 |  |
| [Logs001](https://ambientcg.com/a/Logs001) | Logs | ambientCG | CC0 1.0 | 29.4 |  |
| [Marble012](https://ambientcg.com/a/Marble012) | Marble | ambientCG | CC0 1.0 | 14.8 |  |
| [Marble016](https://ambientcg.com/a/Marble016) | Marble | ambientCG | CC0 1.0 | 11.9 |  |
| [Marble021](https://ambientcg.com/a/Marble021) | Marble | ambientCG | CC0 1.0 | 11.4 |  |
| [Metal007](https://ambientcg.com/a/Metal007) | Metal | ambientCG | CC0 1.0 | 73.1 |  |
| [Metal009](https://ambientcg.com/a/Metal009) | Metal | ambientCG | CC0 1.0 | 70.0 |  |
| [Metal011](https://ambientcg.com/a/Metal011) | Metal | ambientCG | CC0 1.0 | 63.9 |  |
| [Metal027](https://ambientcg.com/a/Metal027) | Metal | ambientCG | CC0 1.0 | 100.4 |  |
| [Metal029](https://ambientcg.com/a/Metal029) | Metal | ambientCG | CC0 1.0 | 93.7 |  |
| [Metal032](https://ambientcg.com/a/Metal032) | Metal | ambientCG | CC0 1.0 | 73.7 |  |
| [Metal034](https://ambientcg.com/a/Metal034) | Metal | ambientCG | CC0 1.0 | 34.8 |  |
| [Metal035](https://ambientcg.com/a/Metal035) | Metal | ambientCG | CC0 1.0 | 54.3 |  |
| [Metal036](https://ambientcg.com/a/Metal036) | Metal | ambientCG | CC0 1.0 | 53.4 |  |
| [Metal038](https://ambientcg.com/a/Metal038) | Metal | ambientCG | CC0 1.0 | 73.3 |  |
| [Metal041A](https://ambientcg.com/a/Metal041A) | Metal | ambientCG | CC0 1.0 | 53.0 |  |
| [Metal042A](https://ambientcg.com/a/Metal042A) | Metal | ambientCG | CC0 1.0 | 33.7 |  |
| [Metal046A](https://ambientcg.com/a/Metal046A) | Metal | ambientCG | CC0 1.0 | 67.1 |  |
| [Metal046B](https://ambientcg.com/a/Metal046B) | Metal | ambientCG | CC0 1.0 | 82.7 |  |
| [Metal047B](https://ambientcg.com/a/Metal047B) | Metal | ambientCG | CC0 1.0 | 72.7 |  |
| [Metal048A](https://ambientcg.com/a/Metal048A) | Metal | ambientCG | CC0 1.0 | 21.4 |  |
| [Metal048B](https://ambientcg.com/a/Metal048B) | Metal | ambientCG | CC0 1.0 | 30.7 |  |
| [Metal048C](https://ambientcg.com/a/Metal048C) | Metal | ambientCG | CC0 1.0 | 43.8 |  |
| [Metal049A](https://ambientcg.com/a/Metal049A) | Metal | ambientCG | CC0 1.0 | 24.7 |  |
| [Metal050A](https://ambientcg.com/a/Metal050A) | Metal | ambientCG | CC0 1.0 | 22.8 |  |
| [Metal052A](https://ambientcg.com/a/Metal052A) | Metal | ambientCG | CC0 1.0 | 23.8 |  |
| [Metal052C](https://ambientcg.com/a/Metal052C) | Metal | ambientCG | CC0 1.0 | 52.4 |  |
| [Metal053B](https://ambientcg.com/a/Metal053B) | Metal | ambientCG | CC0 1.0 | 40.7 |  |
| [Metal053C](https://ambientcg.com/a/Metal053C) | Metal | ambientCG | CC0 1.0 | 58.4 |  |
| [Metal055A](https://ambientcg.com/a/Metal055A) | Metal | ambientCG | CC0 1.0 | 58.3 |  |
| [Metal061A](https://ambientcg.com/a/Metal061A) | Metal | ambientCG | CC0 1.0 | 37.4 |  |
| [Metal061B](https://ambientcg.com/a/Metal061B) | Metal | ambientCG | CC0 1.0 | 48.3 |  |
| [Metal062C](https://ambientcg.com/a/Metal062C) | Metal | ambientCG | CC0 1.0 | 62.4 |  |
| [Metal063](https://ambientcg.com/a/Metal063) | Metal | ambientCG | CC0 1.0 | 65.9 |  |
| [Metal064](https://ambientcg.com/a/Metal064) | Metal | ambientCG | CC0 1.0 | 98.7 |  |
| [MetalPlates004](https://ambientcg.com/a/MetalPlates004) | Metal Plates | ambientCG | CC0 1.0 | 8.0 |  |
| [MetalPlates006](https://ambientcg.com/a/MetalPlates006) | Metal Plates | ambientCG | CC0 1.0 | 13.1 |  |
| [MetalPlates008](https://ambientcg.com/a/MetalPlates008) | Metal Plates | ambientCG | CC0 1.0 | 10.1 |  |
| [MetalPlates013](https://ambientcg.com/a/MetalPlates013) | Metal Plates | ambientCG | CC0 1.0 | 23.1 |  |
| [MetalPlates014](https://ambientcg.com/a/MetalPlates014) | Metal Plates | ambientCG | CC0 1.0 | 14.8 |  |
| [MetalPlates017A](https://ambientcg.com/a/MetalPlates017A) | Metal Plates | ambientCG | CC0 1.0 | 18.3 |  |
| [Moss001](https://ambientcg.com/a/Moss001) | Moss | ambientCG | CC0 1.0 | 37.5 |  |
| [Moss002](https://ambientcg.com/a/Moss002) | Moss | ambientCG | CC0 1.0 | 39.6 |  |
| [Net002A](https://ambientcg.com/a/Net002A) | Net | ambientCG | CC0 1.0 | 16.2 |  |
| [Net004A](https://ambientcg.com/a/Net004A) | Net | ambientCG | CC0 1.0 | 13.4 |  |
| [Onyx013](https://ambientcg.com/a/Onyx013) | Onyx | ambientCG | CC0 1.0 | 12.2 |  |
| [Onyx015](https://ambientcg.com/a/Onyx015) | Onyx | ambientCG | CC0 1.0 | 10.6 |  |
| [PaintedMetal004](https://ambientcg.com/a/PaintedMetal004) | Painted Metal | ambientCG | CC0 1.0 | 81.3 |  |
| [PaintedMetal006](https://ambientcg.com/a/PaintedMetal006) | Painted Metal | ambientCG | CC0 1.0 | 136.9 |  |
| [PaintedMetal009](https://ambientcg.com/a/PaintedMetal009) | Painted Metal | ambientCG | CC0 1.0 | 136.5 |  |
| [PaintedMetal012](https://ambientcg.com/a/PaintedMetal012) | Painted Metal | ambientCG | CC0 1.0 | 109.4 |  |
| [PaintedMetal013](https://ambientcg.com/a/PaintedMetal013) | Painted Metal | ambientCG | CC0 1.0 | 146.1 |  |
| [PaintedMetal016](https://ambientcg.com/a/PaintedMetal016) | Painted Metal | ambientCG | CC0 1.0 | 142.8 |  |
| [PaintedWood007B](https://ambientcg.com/a/PaintedWood007B) | Painted Wood | ambientCG | CC0 1.0 | 29.9 |  |
| [PaintedWood007C](https://ambientcg.com/a/PaintedWood007C) | Painted Wood | ambientCG | CC0 1.0 | 27.9 |  |
| [PaintedWood008C](https://ambientcg.com/a/PaintedWood008C) | Painted Wood | ambientCG | CC0 1.0 | 28.0 |  |
| [PaintedWood009C](https://ambientcg.com/a/PaintedWood009C) | Painted Wood | ambientCG | CC0 1.0 | 28.0 |  |
| [Paper005](https://ambientcg.com/a/Paper005) | Paper | ambientCG | CC0 1.0 | 18.0 |  |
| [Paper006](https://ambientcg.com/a/Paper006) | Paper | ambientCG | CC0 1.0 | 17.9 |  |
| [PavingStones128](https://ambientcg.com/a/PavingStones128) | Paving Stones | ambientCG | CC0 1.0 | 31.9 |  |
| [PavingStones138](https://ambientcg.com/a/PavingStones138) | Paving Stones | ambientCG | CC0 1.0 | 15.3 |  |
| [PavingStones150](https://ambientcg.com/a/PavingStones150) | Paving Stones | ambientCG | CC0 1.0 | 16.1 |  |
| [PavingStones151](https://ambientcg.com/a/PavingStones151) | Paving Stones | ambientCG | CC0 1.0 | 28.8 |  |
| [PavingStones152](https://ambientcg.com/a/PavingStones152) | Paving Stones | ambientCG | CC0 1.0 | 28.4 |  |
| [PavingStones153](https://ambientcg.com/a/PavingStones153) | Paving Stones | ambientCG | CC0 1.0 | 14.2 |  |
| [Planks012](https://ambientcg.com/a/Planks012) | Planks | ambientCG | CC0 1.0 | 108.7 |  |
| [Planks020](https://ambientcg.com/a/Planks020) | Planks | ambientCG | CC0 1.0 | 97.1 |  |
| [Planks021](https://ambientcg.com/a/Planks021) | Planks | ambientCG | CC0 1.0 | 89.6 |  |
| [Planks023A](https://ambientcg.com/a/Planks023A) | Planks | ambientCG | CC0 1.0 | 92.6 |  |
| [Planks023B](https://ambientcg.com/a/Planks023B) | Planks | ambientCG | CC0 1.0 | 93.0 |  |
| [Planks033B](https://ambientcg.com/a/Planks033B) | Planks | ambientCG | CC0 1.0 | 96.8 |  |
| [Planks035B](https://ambientcg.com/a/Planks035B) | Planks | ambientCG | CC0 1.0 | 101.3 |  |
| [Planks036B](https://ambientcg.com/a/Planks036B) | Planks | ambientCG | CC0 1.0 | 90.2 |  |
| [Planks037A](https://ambientcg.com/a/Planks037A) | Planks | ambientCG | CC0 1.0 | 87.9 |  |
| [Planks037B](https://ambientcg.com/a/Planks037B) | Planks | ambientCG | CC0 1.0 | 87.3 |  |
| [Planks039](https://ambientcg.com/a/Planks039) | Planks | ambientCG | CC0 1.0 | 42.7 |  |
| [Planks040](https://ambientcg.com/a/Planks040) | Planks | ambientCG | CC0 1.0 | 99.4 |  |
| [Plaster001](https://ambientcg.com/a/Plaster001) | Plaster | ambientCG | CC0 1.0 | 26.1 |  |
| [Plaster007](https://ambientcg.com/a/Plaster007) | Plaster | ambientCG | CC0 1.0 | 27.9 |  |
| [Rock030](https://ambientcg.com/a/Rock030) | Rock | ambientCG | CC0 1.0 | 33.5 |  |
| [Rock035](https://ambientcg.com/a/Rock035) | Rock | ambientCG | CC0 1.0 | 33.0 |  |
| [Rock051](https://ambientcg.com/a/Rock051) | Rock | ambientCG | CC0 1.0 | 30.4 |  |
| [Rock058](https://ambientcg.com/a/Rock058) | Rock | ambientCG | CC0 1.0 | 27.1 |  |
| [Rock060](https://ambientcg.com/a/Rock060) | Rock | ambientCG | CC0 1.0 | 26.1 |  |
| [Rock061](https://ambientcg.com/a/Rock061) | Rock | ambientCG | CC0 1.0 | 23.6 |  |
| [Rock063](https://ambientcg.com/a/Rock063) | Rock | ambientCG | CC0 1.0 | 14.9 |  |
| [Rock064](https://ambientcg.com/a/Rock064) | Rock | ambientCG | CC0 1.0 | 28.4 |  |
| [Rope001](https://ambientcg.com/a/Rope001) | Rope | ambientCG | CC0 1.0 | 46.0 |  |
| [Rope002](https://ambientcg.com/a/Rope002) | Rope | ambientCG | CC0 1.0 | 48.6 |  |
| [Rope003](https://ambientcg.com/a/Rope003) | Rope | ambientCG | CC0 1.0 | 48.8 |  |
| [Rust004](https://ambientcg.com/a/Rust004) | Rust | ambientCG | CC0 1.0 | 76.5 |  |
| [Rust006](https://ambientcg.com/a/Rust006) | Rust | ambientCG | CC0 1.0 | 114.4 |  |
| [Rust007](https://ambientcg.com/a/Rust007) | Rust | ambientCG | CC0 1.0 | 109.3 |  |
| [Rust008](https://ambientcg.com/a/Rust008) | Rust | ambientCG | CC0 1.0 | 110.1 |  |
| [Rust009](https://ambientcg.com/a/Rust009) | Rust | ambientCG | CC0 1.0 | 117.0 |  |
| [Rust010](https://ambientcg.com/a/Rust010) | Rust | ambientCG | CC0 1.0 | 111.7 |  |
| [Scratches001](https://ambientcg.com/a/Scratches001) | Scratches | ambientCG | CC0 1.0 | 69.1 |  |
| [Scratches002](https://ambientcg.com/a/Scratches002) | Scratches | ambientCG | CC0 1.0 | 43.7 |  |
| [Scratches003](https://ambientcg.com/a/Scratches003) | Scratches | ambientCG | CC0 1.0 | 60.3 |  |
| [Scratches004](https://ambientcg.com/a/Scratches004) | Scratches | ambientCG | CC0 1.0 | 77.6 |  |
| [Scratches005](https://ambientcg.com/a/Scratches005) | Scratches | ambientCG | CC0 1.0 | 80.7 |  |
| [SheetMetal001](https://ambientcg.com/a/SheetMetal001) | Sheet Metal | ambientCG | CC0 1.0 | 15.7 |  |
| [SheetMetal002](https://ambientcg.com/a/SheetMetal002) | Sheet Metal | ambientCG | CC0 1.0 | 14.2 |  |
| [Smear002](https://ambientcg.com/a/Smear002) | Smear | ambientCG | CC0 1.0 | 16.3 |  |
| [Smear005](https://ambientcg.com/a/Smear005) | Smear | ambientCG | CC0 1.0 | 6.3 |  |
| [Smear007](https://ambientcg.com/a/Smear007) | Smear | ambientCG | CC0 1.0 | 29.3 |  |
| [Smear008](https://ambientcg.com/a/Smear008) | Smear | ambientCG | CC0 1.0 | 19.5 |  |
| [Snow014](https://ambientcg.com/a/Snow014) | Snow | ambientCG | CC0 1.0 | 25.2 |  |
| [Snow015](https://ambientcg.com/a/Snow015) | Snow | ambientCG | CC0 1.0 | 34.4 |  |
| [SurfaceImperfections001](https://ambientcg.com/a/SurfaceImperfections001) | Surface Imperfections | ambientCG | CC0 1.0 | 18.1 |  |
| [SurfaceImperfections003](https://ambientcg.com/a/SurfaceImperfections003) | Surface Imperfections | ambientCG | CC0 1.0 | 18.9 |  |
| [SurfaceImperfections013](https://ambientcg.com/a/SurfaceImperfections013) | Surface Imperfections | ambientCG | CC0 1.0 | 23.1 |  |
| [SurfaceImperfections014](https://ambientcg.com/a/SurfaceImperfections014) | Surface Imperfections | ambientCG | CC0 1.0 | 31.4 |  |
| [SurfaceImperfections015](https://ambientcg.com/a/SurfaceImperfections015) | Surface Imperfections | ambientCG | CC0 1.0 | 31.4 |  |
| [SurfaceImperfections016](https://ambientcg.com/a/SurfaceImperfections016) | Surface Imperfections | ambientCG | CC0 1.0 | 31.4 |  |
| [SurfaceImperfections017](https://ambientcg.com/a/SurfaceImperfections017) | Surface Imperfections | ambientCG | CC0 1.0 | 24.0 |  |
| [SurfaceImperfections018](https://ambientcg.com/a/SurfaceImperfections018) | Surface Imperfections | ambientCG | CC0 1.0 | 22.1 |  |
| [SurfaceImperfections019](https://ambientcg.com/a/SurfaceImperfections019) | Surface Imperfections | ambientCG | CC0 1.0 | 23.1 |  |
| [SurfaceImperfections020](https://ambientcg.com/a/SurfaceImperfections020) | Surface Imperfections | ambientCG | CC0 1.0 | 23.7 |  |
| [TreeEnd003](https://ambientcg.com/a/TreeEnd003) | Tree End | ambientCG | CC0 1.0 | 19.5 |  |
| [TreeEnd005](https://ambientcg.com/a/TreeEnd005) | Tree End | ambientCG | CC0 1.0 | 20.4 |  |
| [Wicker010A](https://ambientcg.com/a/Wicker010A) | Wicker | ambientCG | CC0 1.0 | 23.6 |  |
| [Wicker013](https://ambientcg.com/a/Wicker013) | Wicker | ambientCG | CC0 1.0 | 26.3 |  |
| [Wood049](https://ambientcg.com/a/Wood049) | Wood | ambientCG | CC0 1.0 | 23.2 |  |
| [Wood051](https://ambientcg.com/a/Wood051) | Wood | ambientCG | CC0 1.0 | 23.2 |  |
| [Wood058](https://ambientcg.com/a/Wood058) | Wood | ambientCG | CC0 1.0 | 25.5 |  |
| [Wood066](https://ambientcg.com/a/Wood066) | Wood | ambientCG | CC0 1.0 | 23.2 |  |
| [Wood067](https://ambientcg.com/a/Wood067) | Wood | ambientCG | CC0 1.0 | 21.5 |  |
| [Wood092](https://ambientcg.com/a/Wood092) | Wood | ambientCG | CC0 1.0 | 18.2 |  |
| [Wood094](https://ambientcg.com/a/Wood094) | Wood | ambientCG | CC0 1.0 | 14.8 |  |
| [Wood095](https://ambientcg.com/a/Wood095) | Wood | ambientCG | CC0 1.0 | 12.9 |  |
| [Wood096](https://ambientcg.com/a/Wood096) | Wood | ambientCG | CC0 1.0 | 19.6 |  |
| [Wood097](https://ambientcg.com/a/Wood097) | Wood | ambientCG | CC0 1.0 | 15.6 |  |
| [Wood098](https://ambientcg.com/a/Wood098) | Wood | ambientCG | CC0 1.0 | 16.8 |  |
| [Wood099](https://ambientcg.com/a/Wood099) | Wood | ambientCG | CC0 1.0 | 7.6 |  |

### Модели: 82

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [KayKit-Character-Pack-Adventures-1.0](https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0) | low poly | KayKit | CC0 1.0 |  |  |
| [KayKit-Character-Pack-Skeletons-1.0](https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Skeletons-1.0) | low poly | KayKit | CC0 1.0 |  |  |
| [KayKit-Dungeon-Remastered-1.0](https://github.com/KayKit-Game-Assets/KayKit-Dungeon-Remastered-1.0) | low poly | KayKit | CC0 1.0 |  |  |
| [KayKit-Medieval-Hexagon-Pack-1.0](https://github.com/KayKit-Game-Assets/KayKit-Medieval-Hexagon-Pack-1.0) | low poly | KayKit | CC0 1.0 |  |  |
| [3d Greek Weapons Set](https://opengameart.org/content/3d-greek-weapons-set) | 3d-greek-weapons-set | OpenGameArt | CC0 1.0 | 2.3 |  |
| [Bucket Helmet](https://opengameart.org/content/bucket-helmet) | bucket-helmet | OpenGameArt | CC0 1.0 | 0.7 |  |
| [Cethiel's Weapons 3D](https://opengameart.org/content/cethiels-weapons-3d) | cethiels-weapons-3d | OpenGameArt | CC0 1.0 | 2.1 |  |
| [Free 3D Castle / Dungeon Tileset](https://opengameart.org/content/free-3d-castle-dungeon-tileset) | free-3d-castle-dungeon-tileset | OpenGameArt | CC0 1.0 | 12.9 |  |
| [Knight statue](https://opengameart.org/content/knight-statue) | knight-statue | OpenGameArt | CC0 1.0 | 4.4 |  |
| [Low Poly RPG Pack](https://opengameart.org/content/low-poly-rpg-pack) | low-poly-rpg-pack | OpenGameArt | CC0 1.0 | 44.6 |  |
| [LowPoly Medieval Weapons](https://opengameart.org/content/lowpoly-medieval-weapons) | lowpoly-medieval-weapons | OpenGameArt | CC0 1.0 | 3.7 |  |
| [Medieval Weapon Pack](https://opengameart.org/content/medieval-weapon-pack) | medieval-weapon-pack | OpenGameArt | CC0 1.0 | 2.9 |  |
| [Shield & sword](https://opengameart.org/content/shield-sword) | shield-sword | OpenGameArt | CC0 1.0 | 3.8 |  |
| [gothic_statue](https://polyhaven.com/a/gothic_statue) | collection: project_lighthouse, decorative | Poly Haven | CC0 1.0 | 33.9 |  |
| [fishermans_hat](https://polyhaven.com/a/fishermans_hat) | collection: project_lighthouse, props | Poly Haven | CC0 1.0 | 36.3 |  |
| [rubber_boots](https://polyhaven.com/a/rubber_boots) | collection: project_lighthouse, props | Poly Haven | CC0 1.0 | 19.5 |  |
| [wooden_ladder](https://polyhaven.com/a/wooden_ladder) | collection: project_lighthouse, tools, industrial | Poly Haven | CC0 1.0 | 32.3 |  |
| [wine_barrel_01](https://polyhaven.com/a/wine_barrel_01) | containers | Poly Haven | CC0 1.0 | 7.4 |  |
| [wooden_crate_01](https://polyhaven.com/a/wooden_crate_01) | containers, collection: smugglers_cove | Poly Haven | CC0 1.0 | 31.7 |  |
| [metal_jug](https://polyhaven.com/a/metal_jug) | containers, decorative, vases | Poly Haven | CC0 1.0 | 21.7 |  |
| [wooden_barrels_01](https://polyhaven.com/a/wooden_barrels_01) | containers, props, collection: smugglers_cove | Poly Haven | CC0 1.0 | 84.6 |  |
| [wooden_crate_02](https://polyhaven.com/a/wooden_crate_02) | containers, props, collection: smugglers_cove | Poly Haven | CC0 1.0 | 31.3 |  |
| [bull_head](https://polyhaven.com/a/bull_head) | decorative | Poly Haven | CC0 1.0 | 20.1 |  |
| [horse_head](https://polyhaven.com/a/horse_head) | decorative | Poly Haven | CC0 1.0 | 18.5 |  |
| [lion_head](https://polyhaven.com/a/lion_head) | decorative | Poly Haven | CC0 1.0 | 30.9 |  |
| [marble_bust_01](https://polyhaven.com/a/marble_bust_01) | decorative | Poly Haven | CC0 1.0 | 5.8 |  |
| [brass_candleholders](https://polyhaven.com/a/brass_candleholders) | decorative, lighting | Poly Haven | CC0 1.0 | 115.1 |  |
| [brass_diya_lantern](https://polyhaven.com/a/brass_diya_lantern) | decorative, lighting | Poly Haven | CC0 1.0 | 17.6 |  |
| [wooden_candlestick](https://polyhaven.com/a/wooden_candlestick) | decorative, lighting | Poly Haven | CC0 1.0 | 39.1 |  |
| [brass_vase_01](https://polyhaven.com/a/brass_vase_01) | decorative, vases | Poly Haven | CC0 1.0 | 4.7 |  |
| [grass_bermuda_01](https://polyhaven.com/a/grass_bermuda_01) | grass, nature, ground cover, collection: smugglers_cove | Poly Haven | CC0 1.0 | 15.9 |  |
| [barrel_03](https://polyhaven.com/a/barrel_03) | industrial, containers | Poly Haven | CC0 1.0 | 8.0 |  |
| [coastal_cliff_01](https://polyhaven.com/a/coastal_cliff_01) | nature, collection: smugglers_cove | Poly Haven | CC0 1.0 | 38.4 |  |
| [coastal_cliff_02](https://polyhaven.com/a/coastal_cliff_02) | nature, collection: smugglers_cove, collection: verdant_trail | Poly Haven | CC0 1.0 | 59.1 |  |
| [coast_land_rocks_02](https://polyhaven.com/a/coast_land_rocks_02) | nature, rocks, collection: smugglers_cove | Poly Haven | CC0 1.0 | 75.4 |  |
| [coast_land_rocks_03](https://polyhaven.com/a/coast_land_rocks_03) | nature, rocks, collection: smugglers_cove | Poly Haven | CC0 1.0 | 68.3 |  |
| [coast_land_rocks_04](https://polyhaven.com/a/coast_land_rocks_04) | nature, rocks, collection: smugglers_cove | Poly Haven | CC0 1.0 | 69.9 |  |
| [coast_line_01](https://polyhaven.com/a/coast_line_01) | nature, rocks, collection: smugglers_cove | Poly Haven | CC0 1.0 | 50.6 |  |
| [coast_line_02](https://polyhaven.com/a/coast_line_02) | nature, rocks, collection: smugglers_cove | Poly Haven | CC0 1.0 | 56.0 |  |
| [coast_rocks_01](https://polyhaven.com/a/coast_rocks_01) | nature, rocks, collection: smugglers_cove | Poly Haven | CC0 1.0 | 53.1 |  |
| [coast_rocks_02](https://polyhaven.com/a/coast_rocks_02) | nature, rocks, collection: smugglers_cove | Poly Haven | CC0 1.0 | 73.2 |  |
| [coast_rocks_03](https://polyhaven.com/a/coast_rocks_03) | nature, rocks, collection: smugglers_cove | Poly Haven | CC0 1.0 | 59.3 |  |
| [coast_rocks_05](https://polyhaven.com/a/coast_rocks_05) | nature, rocks, collection: smugglers_cove, collection: verdant_trail | Poly Haven | CC0 1.0 | 62.2 |  |
| [coastal_cliff_04](https://polyhaven.com/a/coastal_cliff_04) | nature, rocks, collection: smugglers_cove, collection: verdant_trail | Poly Haven | CC0 1.0 | 79.3 |  |
| [sand_rocks_small_01](https://polyhaven.com/a/sand_rocks_small_01) | nature, rocks, collection: smugglers_cove, collection: verdant_trail | Poly Haven | CC0 1.0 | 55.8 |  |
| [rock_09](https://polyhaven.com/a/rock_09) | nature, rocks, collection: verdant_trail | Poly Haven | CC0 1.0 | 17.5 |  |
| [shrub_sorrel_01](https://polyhaven.com/a/shrub_sorrel_01) | plants, flowers, nature, collection: smugglers_cove | Poly Haven | CC0 1.0 | 11.9 |  |
| [pachira_aquatica_01](https://polyhaven.com/a/pachira_aquatica_01) | plants, nature, collection: smugglers_cove | Poly Haven | CC0 1.0 | 36.3 |  |
| [fern_02](https://polyhaven.com/a/fern_02) | plants, nature, collection: smugglers_cove, collection: pine_forest | Poly Haven | CC0 1.0 | 10.8 |  |
| [anthurium_botany_01](https://polyhaven.com/a/anthurium_botany_01) | plants, nature, collection: the_shed, collection: smugglers_cove | Poly Haven | CC0 1.0 | 20.9 |  |
| [calathea_orbifolia_01](https://polyhaven.com/a/calathea_orbifolia_01) | plants, nature, ground cover, collection: smugglers_cove | Poly Haven | CC0 1.0 | 20.3 |  |
| [antique_estoc](https://polyhaven.com/a/antique_estoc) | props | Poly Haven | CC0 1.0 | 29.2 |  |
| [antique_katana_01](https://polyhaven.com/a/antique_katana_01) | props | Poly Haven | CC0 1.0 | 4.7 |  |
| [ornate_medieval_dagger](https://polyhaven.com/a/ornate_medieval_dagger) | props | Poly Haven | CC0 1.0 | 27.0 |  |
| [ornate_medieval_mace](https://polyhaven.com/a/ornate_medieval_mace) | props | Poly Haven | CC0 1.0 | 28.9 |  |
| [ornate_war_hammer](https://polyhaven.com/a/ornate_war_hammer) | props | Poly Haven | CC0 1.0 | 25.1 |  |
| [wooden_axe](https://polyhaven.com/a/wooden_axe) | props | Poly Haven | CC0 1.0 | 25.5 |  |
| [wooden_axe_02](https://polyhaven.com/a/wooden_axe_02) | props | Poly Haven | CC0 1.0 | 35.7 |  |
| [wooden_handle_saber](https://polyhaven.com/a/wooden_handle_saber) | props, collection: hidden_alley | Poly Haven | CC0 1.0 | 21.2 |  |
| [kite_shield](https://polyhaven.com/a/kite_shield) | props, collection: the_shed | Poly Haven | CC0 1.0 | 56.4 |  |
| [machete](https://polyhaven.com/a/machete) | props, collection: the_shed | Poly Haven | CC0 1.0 | 38.0 |  |
| [wooden_bucket_01](https://polyhaven.com/a/wooden_bucket_01) | props, containers, collection: smugglers_cove | Poly Haven | CC0 1.0 | 31.1 |  |
| [wooden_bucket_02](https://polyhaven.com/a/wooden_bucket_02) | props, containers, collection: smugglers_cove | Poly Haven | CC0 1.0 | 31.6 |  |
| [treasure_chest](https://polyhaven.com/a/treasure_chest) | props, containers, decorative, collection: smugglers_cove | Poly Haven | CC0 1.0 | 42.3 |  |
| [wine_bottles_01](https://polyhaven.com/a/wine_bottles_01) | props, containers, dishes | Poly Haven | CC0 1.0 | 43.5 |  |
| [katana_stand_01](https://polyhaven.com/a/katana_stand_01) | props, decorative | Poly Haven | CC0 1.0 | 7.3 |  |
| [book_encyclopedia_set_01](https://polyhaven.com/a/book_encyclopedia_set_01) | props, decorative, books | Poly Haven | CC0 1.0 | 9.9 |  |
| [wooden_bowl_01](https://polyhaven.com/a/wooden_bowl_01) | props, decorative, dishes | Poly Haven | CC0 1.0 | 25.9 |  |
| [brass_goblets](https://polyhaven.com/a/brass_goblets) | props, dishes, decorative, containers | Poly Haven | CC0 1.0 | 67.2 |  |
| [Lantern_01](https://polyhaven.com/a/Lantern_01) | props, lighting | Poly Haven | CC0 1.0 | 9.8 |  |
| [wooden_lantern_01](https://polyhaven.com/a/wooden_lantern_01) | props, lighting, collection: smugglers_cove | Poly Haven | CC0 1.0 | 54.7 |  |
| [seadogs_compass](https://polyhaven.com/a/seadogs_compass) | props, tools, decorative, collection: project_lighthouse | Poly Haven | CC0 1.0 | 28.1 |  |
| [rock_07](https://polyhaven.com/a/rock_07) | rocks, nature, collection: verdant_trail | Poly Haven | CC0 1.0 | 20.4 |  |
| [rock_face_01](https://polyhaven.com/a/rock_face_01) | rocks, nature, collection: verdant_trail | Poly Haven | CC0 1.0 | 37.0 |  |
| [dutch_ship_large_01](https://polyhaven.com/a/dutch_ship_large_01) | ships, collection: smugglers_cove | Poly Haven | CC0 1.0 | 107.1 |  |
| [dutch_ship_large_02](https://polyhaven.com/a/dutch_ship_large_02) | ships, collection: smugglers_cove | Poly Haven | CC0 1.0 | 106.2 |  |
| [dutch_ship_medium](https://polyhaven.com/a/dutch_ship_medium) | ships, collection: smugglers_cove | Poly Haven | CC0 1.0 | 105.1 |  |
| [ship_pinnace](https://polyhaven.com/a/ship_pinnace) | ships, rigged, collection: smugglers_cove | Poly Haven | CC0 1.0 | 222.6 |  |
| [modular_fort_01](https://polyhaven.com/a/modular_fort_01) | structures, buildings, collection: smugglers_cove | Poly Haven | CC0 1.0 | 131.8 |  |
| [stone_fire_pit](https://polyhaven.com/a/stone_fire_pit) | structures, buildings, furniture, collection: the_shed | Poly Haven | CC0 1.0 | 38.7 |  |
| [modular_wooden_pier](https://polyhaven.com/a/modular_wooden_pier) | structures, collection: smugglers_cove | Poly Haven | CC0 1.0 | 77.7 |  |
| [hatchet](https://polyhaven.com/a/hatchet) | tools | Poly Haven | CC0 1.0 | 26.8 |  |

### Свет (HDRI): 16

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [aft_lounge](https://polyhaven.com/a/aft_lounge) | light | Poly Haven | CC0 1.0 | 26.3 |  |
| [aristea_wreck](https://polyhaven.com/a/aristea_wreck) | light | Poly Haven | CC0 1.0 | 25.3 |  |
| [blue_grotto](https://polyhaven.com/a/blue_grotto) | light | Poly Haven | CC0 1.0 | 28.5 |  |
| [brown_photostudio_02](https://polyhaven.com/a/brown_photostudio_02) | light | Poly Haven | CC0 1.0 | 25.4 |  |
| [burnt_warehouse](https://polyhaven.com/a/burnt_warehouse) | light | Poly Haven | CC0 1.0 | 28.1 |  |
| [cave_wall](https://polyhaven.com/a/cave_wall) | light | Poly Haven | CC0 1.0 | 28.8 |  |
| [circus_arena](https://polyhaven.com/a/circus_arena) | light | Poly Haven | CC0 1.0 | 24.2 |  |
| [drachenfels_cellar](https://polyhaven.com/a/drachenfels_cellar) | light | Poly Haven | CC0 1.0 | 29.3 |  |
| [fireplace](https://polyhaven.com/a/fireplace) | light | Poly Haven | CC0 1.0 | 23.7 |  |
| [forest_cave](https://polyhaven.com/a/forest_cave) | light | Poly Haven | CC0 1.0 | 29.8 |  |
| [golden_bay](https://polyhaven.com/a/golden_bay) | light | Poly Haven | CC0 1.0 | 22.6 |  |
| [photo_studio_loft_hall](https://polyhaven.com/a/photo_studio_loft_hall) | light | Poly Haven | CC0 1.0 | 25.2 |  |
| [small_harbor_01](https://polyhaven.com/a/small_harbor_01) | light | Poly Haven | CC0 1.0 | 25.6 |  |
| [studio_small_08](https://polyhaven.com/a/studio_small_08) | light | Poly Haven | CC0 1.0 | 23.5 |  |
| [studio_small_09](https://polyhaven.com/a/studio_small_09) | light | Poly Haven | CC0 1.0 | 24.7 |  |
| [ulmer_muenster](https://polyhaven.com/a/ulmer_muenster) | light | Poly Haven | CC0 1.0 | 25.1 |  |

### Эффекты: 36

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [Animations - Blood, Hit and Both :D](https://opengameart.org/content/animations-blood-hit-and-both-d) | animations-blood-hit-and-both-d | OpenGameArt | CC0 1.0 | 1.1 |  |
| [Blood Splatters](https://opengameart.org/content/blood-splatters) | blood-splatters | OpenGameArt | CC0 1.0 |  |  |
| [Bloodsplatter and Bloodsplash Animation](https://opengameart.org/content/bloodsplatter-and-bloodsplash-animation) | bloodsplatter-and-bloodsplash-animation | OpenGameArt | CC0 1.0 | 0.5 |  |
| [Free VFX asset pack](https://opengameart.org/content/free-vfx-asset-pack) | free-vfx-asset-pack | OpenGameArt | CC0 на OpenGameArt, CC BY 4.0 на itch.io | 94.6 | указать автора CodeManu |
| [Particle Pack (80+ sprites)](https://opengameart.org/content/particle-pack-80-sprites) | particle-pack-80-sprites | OpenGameArt | CC0 1.0 | 9.8 |  |
| [Slash Effect Collection](https://opengameart.org/content/slash-effect-collection) | slash-effect-collection | OpenGameArt | CC0 1.0 | 3.4 |  |
| [Smoke particle assets](https://opengameart.org/content/smoke-particle-assets) | smoke-particle-assets | OpenGameArt | CC0 1.0 | 13.2 |  |
| [Weapon Slash - Effect](https://opengameart.org/content/weapon-slash-effect) | weapon-slash-effect | OpenGameArt | CC0 1.0 | 3.6 |  |
| [CandleSmoke01-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 1.7 |  |
| [Cloud01-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 3.0 |  |
| [Cloud02-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 3.4 |  |
| [Cloud03-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 3.3 |  |
| [Cloud04-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 3.4 |  |
| [DiscSmoke01-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 8.5 |  |
| [Explosion00-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 3.2 |  |
| [Explosion01-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 3.0 |  |
| [Explosion01-light-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 3.0 |  |
| [Explosion01-light-nofire-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 2.6 |  |
| [Explosion01-nofire-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 2.7 |  |
| [Explosion02-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 3.6 |  |
| [Explosion02HD-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 15.3 |  |
| [FireBall01-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 5.9 |  |
| [FireBall02-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 5.7 |  |
| [FireBall03-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 5.1 |  |
| [FireBall04-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 4.9 |  |
| [Flame02-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 8.8 |  |
| [Flame02-temperature-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 4.3 |  |
| [Flame03-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 2.5 |  |
| [Flame03-hollow-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 9.0 |  |
| [SmallFlame01-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 6.6 |  |
| [SmallFlame01-mini-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 7.1 |  |
| [SmallFlame01-smaller-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 5.0 |  |
| [WispySmoke01-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 4.6 |  |
| [WispySmoke02-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 5.0 |  |
| [WispySmoke03-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 3.6 |  |
| [WispySmoke03b-flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | flipbook | Unity Labs | CC0 1.0 | 3.2 |  |

### 2D и интерфейс: 13

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [Hexagon pack (310x)](https://opengameart.org/content/hexagon-pack-310x) | hexagon-pack-310x | OpenGameArt | CC0 1.0 | 4.4 |  |
| [Isometric Buildings #1](https://opengameart.org/content/isometric-buildings-1) | isometric-buildings-1 | OpenGameArt | CC0 1.0 | 1.7 |  |
| [Isometric Landscape](https://opengameart.org/content/isometric-landscape) | isometric-landscape | OpenGameArt | CC0 1.0 | 1.1 |  |
| [Isometric Miniature Dungeon](https://opengameart.org/content/isometric-miniature-dungeon) | isometric-miniature-dungeon | OpenGameArt | CC0 1.0 | 14.2 |  |
| [Mobile Controls](https://opengameart.org/content/mobile-controls) | mobile-controls | OpenGameArt | CC0 1.0 | 3.1 |  |
| [Pixel UI pack (750 assets)](https://opengameart.org/content/pixel-ui-pack-750-assets) | pixel-ui-pack-750-assets | OpenGameArt | CC0 1.0 | 0.1 |  |
| [Roguelike/RPG pack (1,700+ tiles)](https://opengameart.org/content/roguelikerpg-pack-1700-tiles) | roguelikerpg-pack-1700-tiles | OpenGameArt | CC0 1.0 | 0.7 |  |
| [RPG Item collection 1](https://opengameart.org/content/rpg-item-collection-1) | rpg-item-collection-1 | OpenGameArt | CC0 1.0 | 4.5 |  |
| [RPG Item collection 2](https://opengameart.org/content/rpg-item-collection-2) | rpg-item-collection-2 | OpenGameArt | CC0 1.0 | 6.0 |  |
| [UI Pack](https://opengameart.org/content/ui-pack) | ui-pack | OpenGameArt | CC0 1.0 | 1.2 |  |
| [UI pack: RPG extension](https://opengameart.org/content/ui-pack-rpg-extension) | ui-pack-rpg-extension | OpenGameArt | CC0 1.0 | 0.2 |  |
| [Game-icons.net (SVG)](https://game-icons.net/) | icons | game-icons.net | CC BY 3.0 | 4.2 |  |
| [Tabler Icons](https://tabler.io/icons) | ui icons | npm registry | MIT |  |  |

### Шрифты с кириллицей: 30

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [alegreya](https://github.com/google/fonts/tree/main/ofl/alegreya) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.9 |  |
| [alegreyasanssc](https://github.com/google/fonts/tree/main/ofl/alegreyasanssc) | cyrillic | Google Fonts | SIL OFL 1.1 | 3.8 |  |
| [alegreyasc](https://github.com/google/fonts/tree/main/ofl/alegreyasc) | cyrillic | Google Fonts | SIL OFL 1.1 | 3.8 |  |
| [cormorant](https://github.com/google/fonts/tree/main/ofl/cormorant) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.9 |  |
| [cormorantsc](https://github.com/google/fonts/tree/main/ofl/cormorantsc) | cyrillic | Google Fonts | SIL OFL 1.1 | 3.8 |  |
| [elmessiri](https://github.com/google/fonts/tree/main/ofl/elmessiri) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.1 |  |
| [exo2](https://github.com/google/fonts/tree/main/ofl/exo2) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.6 |  |
| [forum](https://github.com/google/fonts/tree/main/ofl/forum) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.3 |  |
| [handjet](https://github.com/google/fonts/tree/main/ofl/handjet) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.3 |  |
| [kurale](https://github.com/google/fonts/tree/main/ofl/kurale) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.3 |  |
| [ledger](https://github.com/google/fonts/tree/main/ofl/ledger) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.1 |  |
| [manrope](https://github.com/google/fonts/tree/main/ofl/manrope) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.2 |  |
| [neucha](https://github.com/google/fonts/tree/main/ofl/neucha) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.1 |  |
| [oldstandardtt](https://github.com/google/fonts/tree/main/ofl/oldstandardtt) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.8 |  |
| [oranienbaum](https://github.com/google/fonts/tree/main/ofl/oranienbaum) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.1 |  |
| [oswald](https://github.com/google/fonts/tree/main/ofl/oswald) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.2 |  |
| [pattaya](https://github.com/google/fonts/tree/main/ofl/pattaya) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.4 |  |
| [philosopher](https://github.com/google/fonts/tree/main/ofl/philosopher) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.5 |  |
| [pixelifysans](https://github.com/google/fonts/tree/main/ofl/pixelifysans) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.1 |  |
| [playfairdisplaysc](https://github.com/google/fonts/tree/main/ofl/playfairdisplaysc) | cyrillic | Google Fonts | SIL OFL 1.1 | 1.2 |  |
| [prata](https://github.com/google/fonts/tree/main/ofl/prata) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.1 |  |
| [pressstart2p](https://github.com/google/fonts/tree/main/ofl/pressstart2p) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.1 |  |
| [robotocondensed](https://github.com/google/fonts/tree/main/ofl/robotocondensed) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.8 |  |
| [rubik](https://github.com/google/fonts/tree/main/ofl/rubik) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.7 |  |
| [ruslandisplay](https://github.com/google/fonts/tree/main/ofl/ruslandisplay) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.1 |  |
| [russoone](https://github.com/google/fonts/tree/main/ofl/russoone) | cyrillic | Google Fonts | SIL OFL 1.1 |  |  |
| [tektur](https://github.com/google/fonts/tree/main/ofl/tektur) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.2 |  |
| [unbounded](https://github.com/google/fonts/tree/main/ofl/unbounded) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.8 |  |
| [vollkornsc](https://github.com/google/fonts/tree/main/ofl/vollkornsc) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.8 |  |
| [yesevaone](https://github.com/google/fonts/tree/main/ofl/yesevaone) | cyrillic | Google Fonts | SIL OFL 1.1 | 0.1 |  |

### Звуки: 25

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [10 Impact/Shield Blocks](https://opengameart.org/content/10-impactshield-blocks) | 10-impactshield-blocks | OpenGameArt | CC0 1.0 | 0.1 |  |
| [100 CC0 metal and wood SFX](https://opengameart.org/content/100-cc0-metal-and-wood-sfx) | 100-cc0-metal-and-wood-sfx | OpenGameArt | CC0 1.0 | 2.0 |  |
| [100 CC0 SFX](https://opengameart.org/content/100-cc0-sfx) | 100-cc0-sfx | OpenGameArt | CC0 1.0 | 2.9 |  |
| [20 Sword Sound Effects (Attacks and Clashes)](https://opengameart.org/content/20-sword-sound-effects-attacks-and-clashes) | 20-sword-sound-effects-attacks-and-clashes | OpenGameArt | CC0 1.0 | 0.3 |  |
| [3 Melee sounds](https://opengameart.org/content/3-melee-sounds) | 3-melee-sounds | OpenGameArt | CC0 1.0 | 0.2 |  |
| [40 CC0 water / splash / slime SFX](https://opengameart.org/content/40-cc0-water-splash-slime-sfx) | 40-cc0-water-splash-slime-sfx | OpenGameArt | CC0 1.0 | 2.3 |  |
| [50 RPG sound effects](https://opengameart.org/content/50-rpg-sound-effects) | 50-rpg-sound-effects | OpenGameArt | CC0 1.0 | 0.7 |  |
| [51 UI sound effects (buttons, switches and clicks)](https://opengameart.org/content/51-ui-sound-effects-buttons-switches-and-clicks) | 51-ui-sound-effects-buttons-switches-and-clicks | OpenGameArt | CC0 1.0 | 1.4 |  |
| [80 CC0 RPG SFX](https://opengameart.org/content/80-cc0-rpg-sfx) | 80-cc0-rpg-sfx | OpenGameArt | CC0 1.0 | 1.8 |  |
| [85 Short music jingles](https://opengameart.org/content/85-short-music-jingles) | 85-short-music-jingles | OpenGameArt | CC0 1.0 | 1.1 |  |
| [Crowd Shouting/Speaking Ambience](https://opengameart.org/content/crowd-shoutingspeaking-ambience) | crowd-shoutingspeaking-ambience | OpenGameArt | CC0 1.0 | 0.3 |  |
| [Fantasy Weapons and Apparel SFX Library](https://opengameart.org/content/fantasy-weapons-and-apparel-sfx-library) | fantasy-weapons-and-apparel-sfx-library | OpenGameArt | CC0 1.0 | 12.6 |  |
| [Fantozzi's Footsteps (Grass/Sand & Stone)](https://opengameart.org/content/fantozzis-footsteps-grasssand-stone) | fantozzis-footsteps-grasssand-stone | OpenGameArt | CC0 1.0 | 0.5 |  |
| [Female Hurt Grunts & Groans](https://opengameart.org/content/female-hurt-grunts-groans) | female-hurt-grunts-groans | OpenGameArt | CC0 1.0 | 0.2 |  |
| [Fireplace Sound loop](https://opengameart.org/content/fireplace-sound-loop) | fireplace-sound-loop | OpenGameArt | CC0 1.0 | 10.3 |  |
| [Footsteps Leather, Cloth, Armor](https://opengameart.org/content/footsteps-leather-cloth-armor) | footsteps-leather-cloth-armor | OpenGameArt | CC0 1.0 | 0.1 |  |
| [grunts of male death and pain](https://opengameart.org/content/grunts-male-death-and-pain) | grunts-male-death-and-pain | OpenGameArt | CC0 1.0 | 4.4 |  |
| [Interface Sounds](https://opengameart.org/content/interface-sounds) | interface-sounds | OpenGameArt | CC0 1.0 | 0.8 |  |
| [Magic Spell SFX](https://opengameart.org/content/magic-spell-sfx) | magic-spell-sfx | OpenGameArt | CC0 1.0 | 0.3 |  |
| [Medieval sound effects - Weapon impacts](https://opengameart.org/content/medieval-sound-effects-weapon-impacts) | medieval-sound-effects-weapon-impacts | OpenGameArt | CC0 1.0 | 155.9 |  |
| [Punch](https://opengameart.org/content/punch) | punch | OpenGameArt | CC0 1.0 | 0.2 |  |
| [rain and thunders](https://opengameart.org/content/rain-and-thunders) | rain-and-thunders | OpenGameArt | CC0 1.0 | 6.8 |  |
| [RPG Sound Pack](https://opengameart.org/content/rpg-sound-pack) | rpg-sound-pack | OpenGameArt | CC0 1.0 | 12.5 |  |
| [Swishes Sound Pack](https://opengameart.org/content/swishes-sound-pack) | swishes-sound-pack | OpenGameArt | CC0 1.0 | 0.4 |  |
| [Voiceover Pack: Fighter (40+ taunts)](https://opengameart.org/content/voiceover-pack-fighter-40-taunts) | voiceover-pack-fighter-40-taunts | OpenGameArt | CC0 1.0 | 1.3 |  |

### Музыка: 14

| Название | Что это | Источник | Лицензия | МБ | Примечание |
|---|---|---|---|---:|---|
| [Battle Theme A](https://opengameart.org/content/battle-theme-a) | battle-theme-a | OpenGameArt | CC0 1.0 | 3.3 |  |
| [Boss Battle Music](https://opengameart.org/content/boss-battle-music) | boss-battle-music | OpenGameArt | CC0 1.0 | 21.8 |  |
| [Cave Theme](https://opengameart.org/content/cave-theme) | cave-theme | OpenGameArt | CC0 1.0 | 3.2 |  |
| [Dungeon Ambience](https://opengameart.org/content/dungeon-ambience) | dungeon-ambience | OpenGameArt | CC0 1.0 | 1.2 |  |
| [Evil Approach](https://opengameart.org/content/evil-approach) | evil-approach | OpenGameArt | CC0 1.0 | 19.5 |  |
| [Fast fight / battle music](https://opengameart.org/content/fast-fight-battle-music) | fast-fight-battle-music | OpenGameArt | CC0 1.0 | 5.2 |  |
| [Pirates Incoming](https://opengameart.org/content/pirates-incoming) | pirates-incoming | OpenGameArt | CC0 1.0 | 2.0 |  |
| [QaziJamJam (orchestral battle theme)](https://opengameart.org/content/qazijamjam-orchestral-battle-theme) | qazijamjam-orchestral-battle-theme | OpenGameArt | CC0 1.0 | 41.3 |  |
| [The Epic Adventure (album)](https://opengameart.org/content/the-epic-adventure-album) | the-epic-adventure-album | OpenGameArt | CC0 1.0 | 323.7 |  |
| [The Hope](https://opengameart.org/content/the-hope) | the-hope | OpenGameArt | CC0 1.0 | 5.3 |  |
| [Town Theme RPG](https://opengameart.org/content/town-theme-rpg) | town-theme-rpg | OpenGameArt | CC0 1.0 | 1.3 |  |
| [Tragic ambient main menu](https://opengameart.org/content/tragic-ambient-main-menu) | tragic-ambient-main-menu | OpenGameArt | CC0 1.0 | 2.0 |  |
| [Victory](https://opengameart.org/content/victory) | victory | OpenGameArt | CC0 1.0 | 0.5 |  |
| [Victory Fanfare Short](https://opengameart.org/content/victory-fanfare-short) | victory-fanfare-short | OpenGameArt | CC0 1.0 | 2.1 |  |

## Не брать

Чужие персонажи в паках MakeHuman: green_tomato_rei_ayanami, green_tomato_yoko_tsuno, slayer227_spider-gwen, punkduck_p-ivy_weapon, jaldmic_houndoom_horns, jaldmic_toriel_horns, freezychan_lucoa_quetzalcoatl_horns, sonntag78_junglebook_hair, culturalibre_dr_manhattan, culturalibre_tigra_skin, culturalibre_tigra_white_skin, reizibarrientos_white_walker_skin.

В файле указана AGPL, а в каталоге CC0 или CC BY, не использовать без проверки: blindsaypatten_uniform_skin_texture, callharvey3d_midtoned_female, culturalibre_hair_01, culturalibre_hair_02, culturalibre_hero-heroine_gloves_1, elvs_double_mh_braid, elvs_french_braid_variation, elvs_unkempt_french_braid, elvs_witchy_hallows_hat1, elvs_witchy_lil_bob, ews_striped_shirt, frankyaye_mini_skirt_01, frankyaye_mini_skirt_02, freezychan_lucoa_quetzalcoatl_horns, grinsegold_beard_sigmund_wip, grinsegold_corinthian_helmet, grinsegold_female_pirate_boots, grinsegold_full_beard, grinsegold_mars_suit, grinsegold_moustache, grinsegold_uncle_joshis_hat, grinsegold_wig_bow_tie, grinsegold_wig_bun_blonde_braids, jaldmic_akm_base, jaldmic_demon_horns, jaldmic_houndoom_horns, jaldmic_l1a1, jaldmic_m1911a1, jaldmic_m1951_72, jaldmic_toriel_horns, javherre_casco_caballero_templario_templar_knight_helmet, jujube_bag_on_head, jujube_newsboy_cap, learning_anime_hair, learning_mma_fighting_gloves, littleright_bobcut_hair, maciekg_hammer, maciekg_horned_helmet, maciekg_leather_boots, maciekg_leather_helmet, maciekg_short_bow, maciekg_wizard_hat, maciekg_wizard_robe, male_casualsuit01, male_elegantsuit01, o4saken_dagger, ponytail01, punkduck_alpha7_curly, punkduck_alpha7_curly2, punkduck_alpha7_long, punkduck_alpha7_long2, punkduck_p-ivy_weapon, rehmanpolanski_hair_bun_brown, rehmanpolanski_skin_viking_tattoos, scailman_gogo_platform_boots, scailman_low-heeled_boots, scailman_semitransparent_water_boots, short02, short04, skalldyrssuppe_tube_top_funky_colors, sonntag78_blond_with_headband, sonntag78_junglebook_hair, tiomegamanx_skintight_body_suit_female, titleknown_trans_flag, wdg_scruffy_beard.
