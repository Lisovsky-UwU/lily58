# Lily58 - прошивка

Своя Vial-прошивка для Lily58: раскладка из Vial зашита дефолтом, на вертикальных OLED слева модификаторы, справа слой, WPM и анимация волшебницы.

## Железо

| Что | Как есть |
|---|---|
| Плата | Lily58 rev1, USB `VID_04D8&PID_EB2D`, Vial UID `7E FD FC 5B 7D 39 48 06` |
| Контроллеры | RP2040-клоны Pro Micro, сборка с `CONVERT_TO = rp2040_ce` |
| Загрузчик | RP2040 boot ROM: после reset появляется USB-диск `RPI-RP2` |
| Мастер | левая половинка (`MASTER_LEFT`), USB подключается к ней |
| OLED | SSD1306 128x32, стоят вертикально, оба модуля пинами к пользователю, поэтому на обеих половинках `OLED_ROTATION_270` |

Не Pro Micro на ATmega32u4, хотя исходный Vial-keymap (`keyboards/lily58/rev1/keymaps/vial`) написан под него. QMK Toolbox такие платы не шьет.

## Экраны

Экран после поворота 32x128, строка текста - 5 символов.

- Левый: ` CTL `, ` SFT `, ` ALT `, ` GUI `, ` CPS ` (Caps Lock). Активный подсвечен инверсией.
- Правый: сверху `LAYER` + имя слоя и `WPM` + число, ниже (строки 5-15) один из режимов. Переключение по кругу клавишей `OLED_NEXT` (по умолчанию Nav + место `Q`; в Vial - вкладка "User", `OLED`). Выбор хранится в `eeconfig_user` и переживает отключение.
  1. Волшебница, спрайт 32x88 (`mage_frames.h`): до 5 WPM стоит, хвостики и камень посоха мерцают; 6-40 WPM колдует, искры у посоха; больше 40 WPM цветы у ног; 15 с без нажатий спит; Shift - прыжок, Caps Lock - "!".
  2. Luna (`luna_frames.h`): до 10 WPM сидит, до 40 идет, дальше бежит; Ctrl - крадется, Shift - прыжок, Caps Lock - лает.
  3. Статистика: `TIME` - время с подключения, `KEYS` - нажатия с подключения, график WPM за 64 с (столбик раз в 2 с, полная высота = 120 WPM).
  4. Трек: весь экран, без слоя и WPM, текст повернут на 90 градусов (виртуальный экран 128x32, читается сверху вниз, 4 строки по 21 символу; шрифт рисуется попиксельно в `vline()`). Строки: `PLAY`/`PAUSE` и громкость (или `MUTE`), полоска громкости, название, исполнитель. Строки длиннее 21 символа прокручиваются. Данные шлет скрипт на ПК, без него на экране `NO DATA FROM PC`.

Правая половинка ничего не знает о нажатиях: слой, модификаторы, WPM, Caps и активность ей передает мастер (`SPLIT_*_ENABLE` в `keymap/config.h`). Режим, счетчик нажатий и данные о треке мастер отправляет своей транзакцией `USER_SHARED_SYNC` (структура `shared_state_t` в `keymap.c`, буфер `RPC_M2S_BUFFER_SIZE 80`), при изменении и раз в секунду.

## Скрипт на ПК (режим "Трек")

`host/oled_feed.py` раз в секунду читает громкость системы (pycaw) и текущее медиа Windows (Media Session - то, что видно в плашке над громкостью), переводит кириллицу в латиницу (в шрифте экрана только ASCII) и шлет на клавиатуру по raw HID - тот же интерфейс, что у Vial. Если клавиатуру отключить, переподключается сам.

```
uv run --python cpython-3.13-windows-x86_64-none host/oled_feed.py            # работа
uv run --python cpython-3.13-windows-x86_64-none host/oled_feed.py --dry-run  # только печать, без клавиатуры
```

Python указан явно: без этого uv на этой машине берет 32-битный 3.13, а под него не собирается `psutil` (зависимость pycaw).

Автозапуск: ярлык `Lily58 OLED feed.lnk` в папке автозагрузки (`shell:startup`) запускает скрипт через `uvw` (без окна консоли) с `--log C:\dev\lily58\host\oled_feed.log` - туда пишутся старт и ошибки. Остановить: завершить процессы `uvw.exe`/`python.exe` с `oled_feed` в командной строке; отключить автозапуск: удалить ярлык.

Протокол (пакеты по 32 байта, обрабатывает `raw_hid_receive_kb` в `keymap.c`):

| Байты | Смысл |
|---|---|
| `40 01 vol flags len` | громкость 0-100, flags: `01` играет, `02` звук выключен; `len` - длина текста, начинает новый текст |
| `40 02 off n chars...` | кусок текста до 28 символов со смещения `off` |

Текст: название, байт `1F`, исполнитель (без исполнителя - только название), всего до 64 символов ASCII.

Прошивка отвечает тем же пакетом с `00` во втором байте. Ответ `FF` в первом байте значит, что на клавиатуре старая прошивка без этой команды. Данные считаются свежими 5 с после последнего пакета.

Анимация перерисовывается постоянно, а каждая перерисовка включает экран, поэтому таймаут гашения правого экрана проверяется вручную в `oled_task_user`.

## Раскладка и Vial

Дефолтная раскладка в `keymap/keymap.c` - снимок того, что было настроено в Vial 26.10.2026 (сырой дамп: `backup/keymap_backup.json`). 4 слоя: QWERTY, Colemak, Sym/Num, Nav. Слой Colemak сейчас ничем не включается.

Vial при каждой сборке генерирует случайный `BUILD_ID` и по нему проверяет EEPROM. Поэтому **любая перепрошивка сбрасывает настройки Vial** к раскладке из `keymap.c`. Если что-то поменял в Vial и хочешь сохранить:

```
uv run --no-project --with hidapi python -I tools/vial_dump.py backup/keymap_backup.json
```

затем в WSL `python3 tools/gen_layers.py ~/keeb/vial-qmk backup/keymap_backup.json` и перенеси вывод в `keymap.c`.

## Сборка (WSL Ubuntu-26.04)

Один раз:

```
sudo apt-get install -y make gcc-arm-none-eabi binutils-arm-none-eabi libnewlib-arm-none-eabi python3-venv
mkdir -p ~/keeb && cd ~/keeb
git clone --depth 1 https://github.com/vial-kb/vial-qmk.git
cd vial-qmk && git submodule update --init --depth 1
python3 -m venv ~/keeb/venv && ~/keeb/venv/bin/pip install -r requirements.txt
```

Сборка:

```
bash /mnt/c/dev/lily58/tools/build.sh
```

Скрипт подключает папку `keymap/` в клон как `keyboards/lily58/rev1/keymaps/tokimen` (симлинк) и кладет результат в `build/lily58_rev1_tokimen.uf2`. Пути к клону и venv можно переопределить через `QMK` и `VENV`.

## Прошивка

Одна и та же прошивка на обе половинки, шить по очереди:

1. USB в половинку, которую шьешь. TRRS между половинками лучше отключить.
2. Нажать reset - появится диск `RPI-RP2`.
3. Скопировать на него `build/lily58_rev1_tokimen.uf2`, плата перезагрузится сама.

Или из PowerShell ждать диск и копировать автоматически:

```
.\tools\flash.ps1 -Uf2 .\build\lily58_rev1_tokimen.uf2
```

После обеих половинок: USB обратно в левую, подключить TRRS.

## Спрайты

`sprites/mage/` - волшебница по чужому пиксель-арту (сетка 64x64). Сама картинка `reference.jpg` в репозиторий не входит (лежит локально, в `.gitignore`); снятая с нее сетка уже сохранена в `cells.json`, так что без картинки шаг `grid.py` можно пропустить:

```
cd sprites/mage
uv run --no-project --with pillow --with numpy python -I grid.py   # reference.jpg -> cells.json
uv run --no-project --with pillow python -I mage.py                # cells.json -> mage.json + mage.png
python -I make_header.py                                           # mage.json -> keymap/mage_frames.h
```

В `mage.py`: какие цвета светятся, сдвиг хвостиков под ширину 32, новый посох и эффекты по состояниям.

`sprites/girl/` - черновик аниме-девочки во весь вертикальный экран 32x128, в прошивку не подключен.

## Превью

`preview/lily58-oled.html` - эмулятор обоих экранов с теми же кадрами и шрифтом (`glcdfont_lily.c`), опубликован как https://claude.ai/artifact/V28vtTZUi9W1h5QPh9fzRJ. Пересборка после изменения спрайтов: `cd preview && python -I build_v.py`.

`pick.json` - кадры Luna и утки, вытащенные из `vial-qmk` скриптами `scan.py` и `extract.py`.

## Утилиты

- `tools/vial_id.py` - спросить у клавиатуры версию протокола Vial и UID.
- `tools/vial_dump.py` - снять раскладку, tap dance и макросы по raw HID (только чтение).
- `tools/gen_layers.py` - превратить дамп в блоки `LAYOUT(...)` с именами кейкодов QMK.
