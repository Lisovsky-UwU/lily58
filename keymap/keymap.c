#include QMK_KEYBOARD_H
#include <stdio.h>
#include <string.h>
#include "transactions.h"

enum layer_number {
  _QWERTY = 0,
  _COLEMAK,
  _SYM,
  _NAV
};

// QK_KB_0 is what Vial shows as the first entry of customKeycodes in vial.json (the "User" tab)
enum custom_keycodes {
  OLED_NEXT = QK_KB_0,  // next mode of the right screen
};

// Defaults are a copy of the layout that was configured in Vial before reflashing
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {

[_QWERTY] = LAYOUT(
  KC_ESC  , KC_1    , KC_2    , KC_3    , KC_4    , KC_5    ,                     KC_6    , KC_7    , KC_8    , KC_9    , KC_0    , KC_EQL  ,
  KC_TAB  , KC_Q    , KC_W    , KC_E    , KC_R    , KC_T    ,                     KC_Y    , KC_U    , KC_I    , KC_O    , KC_P    , KC_LBRC ,
  KC_LALT , KC_A    , KC_S    , KC_D    , KC_F    , KC_G    ,                     KC_H    , KC_J    , KC_K    , KC_L    , KC_SCLN , KC_RBRC ,
  KC_LSFT , KC_Z    , KC_X    , KC_C    , KC_V    , KC_B    , KC_DEL  , KC_BSPC , KC_N    , KC_M    , KC_COMM , KC_DOT  , KC_SLSH , KC_QUOT ,
                      KC_LGUI , KC_LCTL , MO(_SYM), KC_SPC  ,                     KC_ENT  , MO(_NAV), KC_CAPS , KC_LALT
),

[_COLEMAK] = LAYOUT(
  KC_GRV  , KC_1    , KC_2    , KC_3    , KC_4    , KC_5    ,                     KC_6    , KC_7    , KC_8    , KC_9    , KC_0    , KC_EQL  ,
  KC_ESC  , KC_Q    , KC_W    , KC_F    , KC_P    , KC_B    ,                     KC_J    , KC_L    , KC_U    , KC_Y    , KC_SCLN , KC_LBRC ,
  KC_TAB  , KC_A    , KC_R    , KC_S    , KC_T    , KC_G    ,                     KC_M    , KC_N    , KC_E    , KC_I    , KC_O    , KC_RBRC ,
  KC_LSFT , KC_Z    , KC_X    , KC_C    , KC_D    , KC_V    , KC_DEL  , KC_MINS , KC_K    , KC_H    , KC_COMM , KC_DOT  , KC_SLSH , KC_QUOT ,
                      KC_LGUI , KC_LCTL , MO(_SYM), KC_SPC  ,                     KC_ENT  , MO(_NAV), KC_BSPC , KC_LALT
),

[_SYM] = LAYOUT(
  KC_GRV  , KC_F1   , KC_F2   , KC_F3   , KC_F4   , KC_F5   ,                     KC_F6   , KC_F7   , KC_F8   , KC_F9   , KC_F10  , KC_F11  ,
  KC_CAPS , KC_QUES , KC_LPRN , KC_SLSH , KC_RPRN , KC_PMNS ,                     KC_NUM  , KC_P7   , KC_P8   , KC_P9   , KC_PPLS , KC_F12  ,
  KC_PDOT , KC_EXLM , KC_LBRC , KC_BSLS , KC_RBRC , KC_UNDS ,                     KC_PAST , KC_P4   , KC_P5   , KC_P6   , KC_P0   , KC_PEQL ,
  KC_LSFT , KC_HASH , KC_LCBR , KC_PIPE , KC_RCBR , KC_SCLN , _______ , _______ , KC_PSLS , KC_P1   , KC_P2   , KC_P3   , KC_PMNS , KC_PDOT ,
                      _______ , _______ , _______ , _______ ,                     _______ , _______ , _______ , _______
),

[_NAV] = LAYOUT(
  XXXXXXX , XXXXXXX , XXXXXXX , XXXXXXX , XXXXXXX , XXXXXXX ,                     XXXXXXX , XXXXXXX , XXXXXXX , XXXXXXX , XXXXXXX , XXXXXXX ,
  XXXXXXX , OLED_NEXT,XXXXXXX , XXXXXXX , XXXXXXX , XXXXXXX ,                     MS_WHLU , KC_HOME , KC_END  , XXXXXXX , KC_MUTE , XXXXXXX ,
  _______ , XXXXXXX , XXXXXXX , XXXXXXX , XXXXXXX , XXXXXXX ,                     KC_LEFT , KC_DOWN , KC_UP   , KC_RGHT , KC_VOLU , KC_PGUP ,
  _______ , XXXXXXX , XXXXXXX , XXXXXXX , XXXXXXX , XXXXXXX , _______ , XXXXXXX , MS_WHLD , KC_MPRV , KC_MPLY , KC_MNXT , KC_VOLD , KC_PGDN ,
                      _______ , _______ , _______ , _______ ,                     _______ , _______ , _______ , _______
)
};

/* State shared with the right half.
   Keypresses, the mode key and data from the PC all arrive at the master (left half);
   the right half only draws, so the master sends it this struct over the TRRS link. */

enum right_mode {
  MODE_MAGE = 0,
  MODE_LUNA,
  MODE_STATS,
  MODE_MEDIA,
  MODE_COUNT
};

#define MEDIA_TITLE_LEN 64
#define MEDIA_PLAYING   0x01
#define MEDIA_MUTED     0x02
#define MEDIA_FRESH     0x80  // the PC script has sent data recently

typedef struct {
  uint8_t  mode;
  uint8_t  volume;  // 0..100
  uint8_t  flags;
  uint8_t  reserved;
  uint32_t keys;    // keypresses since the keyboard was plugged in
  char     title[MEDIA_TITLE_LEN + 1];
} shared_state_t;

static shared_state_t shared = {0};

static void shared_sync_slave_handler(uint8_t in_len, const void *in_data, uint8_t out_len, void *out_data) {
  if (in_len == sizeof(shared)) memcpy(&shared, in_data, sizeof(shared));
}

void keyboard_post_init_user(void) {
  uint32_t saved = eeconfig_read_user();
  shared.mode = saved < MODE_COUNT ? saved : MODE_MAGE;
  transaction_register_rpc(USER_SHARED_SYNC, shared_sync_slave_handler);
}

bool process_record_user(uint16_t keycode, keyrecord_t *record) {
  if (!record->event.pressed) return true;
  shared.keys++;
  if (keycode == OLED_NEXT) {
    shared.mode = (shared.mode + 1) % MODE_COUNT;
    eeconfig_update_user(shared.mode);
    return false;
  }
  return true;
}

/* Data from the PC script (host/oled_feed.py) over the same raw HID interface Vial uses.
   Packets are 32 bytes:
     0x40 0x01 volume flags title_len      - media header, starts a new title
     0x40 0x02 offset count chars[count]   - piece of the title (ASCII only, the font has nothing else) */

#define HID_CMD_MEDIA     0x40
#define HID_MEDIA_HEADER  0x01
#define HID_MEDIA_TITLE   0x02
#define MEDIA_STALE_MS    5000

static char     pending_title[MEDIA_TITLE_LEN + 1];
static uint8_t  pending_len = 0;
static uint32_t media_timer = 0;
static bool     media_seen = false;

void raw_hid_receive_kb(uint8_t *data, uint8_t length) {
  if (data[0] != HID_CMD_MEDIA) {
    data[0] = id_unhandled;
    return;
  }
  if (data[1] == HID_MEDIA_HEADER) {
    shared.volume = data[2] > 100 ? 100 : data[2];
    shared.flags = (shared.flags & MEDIA_FRESH) | (data[3] & (MEDIA_PLAYING | MEDIA_MUTED));
    pending_len = data[4] > MEDIA_TITLE_LEN ? MEDIA_TITLE_LEN : data[4];
    memset(pending_title, 0, sizeof(pending_title));
    if (pending_len == 0) shared.title[0] = 0;
    media_timer = timer_read32();
    media_seen = true;
  } else if (data[1] == HID_MEDIA_TITLE) {
    uint8_t offset = data[2], count = data[3];
    if (offset < pending_len && count <= length - 4) {
      if (offset + count > pending_len) count = pending_len - offset;
      memcpy(pending_title + offset, data + 4, count);
      if (offset + count == pending_len) memcpy(shared.title, pending_title, sizeof(shared.title));
    }
  }
  data[1] = 0x00;  // ack, the buffer goes back to the PC as is
}

void housekeeping_task_user(void) {
  if (!is_keyboard_master()) return;

  if (media_seen && timer_elapsed32(media_timer) < MEDIA_STALE_MS) {
    shared.flags |= MEDIA_FRESH;
  } else {
    shared.flags &= ~MEDIA_FRESH;
  }

  // send on change, but not more often than every 100 ms; resend every second in case the slave rebooted
  static shared_state_t last_sent;
  static uint32_t last_sync = 0;
  bool changed = memcmp(&shared, &last_sent, sizeof(shared)) != 0;
  if ((changed && timer_elapsed32(last_sync) > 100) || timer_elapsed32(last_sync) > 1000) {
    if (transaction_rpc_send(USER_SHARED_SYNC, sizeof(shared), &shared)) {
      last_sent = shared;
      last_sync = timer_read32();
    }
  }
}

#ifdef OLED_ENABLE

// Both screens stand vertically and the modules are mounted the same way (pins towards the user),
// so both halves use the same rotation: 32x128, top of the image away from the user
oled_rotation_t oled_init_user(oled_rotation_t rotation) {
  return OLED_ROTATION_270;
}

/* Left (master): modifiers and Caps Lock, an active one is shown inverted */

static void render_mods(void) {
  uint8_t mods = get_mods();
  oled_set_cursor(0, 1);
  oled_write_P(PSTR(" CTL "), mods & MOD_MASK_CTRL);
  oled_set_cursor(0, 3);
  oled_write_P(PSTR(" SFT "), mods & MOD_MASK_SHIFT);
  oled_set_cursor(0, 5);
  oled_write_P(PSTR(" ALT "), mods & MOD_MASK_ALT);
  oled_set_cursor(0, 7);
  oled_write_P(PSTR(" GUI "), mods & MOD_MASK_GUI);
  oled_set_cursor(0, 10);
  oled_write_P(PSTR(" CPS "), host_keyboard_led_state().caps_lock);
}

/* Right (slave): layer and WPM on rows 0-4, the selected mode on rows 5-15 */

#define AREA_ROW   5
#define AREA_ROWS  11
#define AREA_TOP_Y (AREA_ROW * 8)
#define SCREEN_W   32
#define SCREEN_H   128

static void render_layer_wpm(void) {
  oled_set_cursor(0, 0);
  oled_write_P(PSTR("LAYER"), false);
  oled_set_cursor(0, 1);
  switch (get_highest_layer(layer_state | default_layer_state)) {
    case _QWERTY:  oled_write_P(PSTR("QWRTY"), false); break;
    case _COLEMAK: oled_write_P(PSTR("CLMAK"), false); break;
    case _SYM:     oled_write_P(PSTR("SYM  "), false); break;
    case _NAV:     oled_write_P(PSTR("NAV  "), false); break;
    default:       oled_write_P(PSTR("?    "), false); break;
  }
  oled_set_cursor(0, 3);
  oled_write_P(PSTR("WPM"), false);
  oled_set_cursor(0, 4);
  oled_write(get_u8_str(get_current_wpm(), ' '), false);
}

static void clear_rows(uint8_t first, uint8_t last) {
  static const char blank[SCREEN_W] = {0};
  for (uint8_t row = first; row <= last; row++) {
    oled_set_cursor(0, row);
    oled_write_raw(blank, sizeof(blank));
  }
}

static void write_row(uint8_t row, const char *text) {
  char line[6];
  snprintf(line, sizeof(line), "%-5s", text);  // pad to the full row so old text is wiped
  oled_set_cursor(0, row);
  oled_write(line, false);
}

/* Mode: mage */

#define MAGE_FRAME_DURATION 250
#define MAGE_SIZE           352    // 32x88 px: rows 5..15
#define MAGE_CAST_SPEED     5      // wpm above this: casting, sparks around the staff
#define MAGE_FAST_SPEED     40     // wpm above this: flowers at her feet
#define MAGE_SLEEP_MS       15000  // falls asleep after this long without keypresses

#include "mage_frames.h"

// idle: mostly still, now and then the tails flutter or the gem twinkles
static const uint8_t mage_idle_seq[] = {0, 0, 0, 0, 1, 1, 0, 0, 0, 2, 2};

static void render_mage(bool restart) {
  static uint32_t anim_timer = 0;
  static uint8_t tick = 0;

  if (!restart && timer_elapsed32(anim_timer) < MAGE_FRAME_DURATION) return;
  anim_timer = timer_read32();
  tick++;

  uint8_t mods = get_mods();
  uint8_t wpm = get_current_wpm();
  const char *frame;
  // Shift and Caps come from the master: keypresses themselves never reach this half
  if (host_keyboard_led_state().caps_lock) {
    frame = mage_caps[0];
  } else if (mods & MOD_MASK_SHIFT) {
    frame = mage_jump[0];
  } else if (wpm == 0 && last_input_activity_elapsed() > MAGE_SLEEP_MS) {
    frame = mage_sleep[(tick / 3) % 2];
  } else if (wpm <= MAGE_CAST_SPEED) {
    frame = mage_idle[mage_idle_seq[tick % sizeof(mage_idle_seq)]];
  } else if (wpm <= MAGE_FAST_SPEED) {
    frame = mage_cast[tick % 2];
  } else {
    frame = mage_fast[tick % 2];
  }

  oled_set_cursor(0, AREA_ROW);
  oled_write_raw_P(frame, MAGE_SIZE);
}

/* Mode: Luna the dog by HellSingCoder */

#define LUNA_FRAME_DURATION 200
#define ANIM_SIZE           96  // 32x24 px: 3 rows
#define LUNA_ROW            13  // bottom 3 rows; row 12 is free for the jump
#define LUNA_WALK_SPEED     10
#define LUNA_RUN_SPEED      40

#include "luna_frames.h"

static void render_luna(bool restart) {
  static uint32_t anim_timer = 0;
  static uint8_t current_frame = 0;

  if (!restart && timer_elapsed32(anim_timer) < LUNA_FRAME_DURATION) return;
  anim_timer = timer_read32();
  current_frame = (current_frame + 1) % 2;

  uint8_t mods = get_mods();
  uint8_t wpm = get_current_wpm();
  const char *frame;
  if (host_keyboard_led_state().caps_lock) {
    frame = bark[current_frame];
  } else if (mods & MOD_MASK_CTRL) {
    frame = sneak[current_frame];
  } else if (wpm <= LUNA_WALK_SPEED) {
    frame = sit[current_frame];
  } else if (wpm <= LUNA_RUN_SPEED) {
    frame = walk[current_frame];
  } else {
    frame = run[current_frame];
  }

  bool jump = mods & MOD_MASK_SHIFT;
  clear_rows(jump ? LUNA_ROW + 2 : LUNA_ROW - 1, jump ? LUNA_ROW + 2 : LUNA_ROW - 1);  // the row she has just left
  oled_set_cursor(0, jump ? LUNA_ROW - 1 : LUNA_ROW);
  oled_write_raw_P(frame, ANIM_SIZE);
}

/* Mode: stats - time since plugged in, keypresses, WPM history */

#define WPM_SAMPLE_MS  2000  // one bar per 2 s: the graph shows the last 64 s
#define GRAPH_TOP_Y    88    // rows 11..15
#define GRAPH_H        40
#define GRAPH_MAX_WPM  120   // a full-height bar

static uint8_t wpm_history[SCREEN_W];  // oldest first

// runs in every mode, so the graph already has data when the mode is switched on
static void sample_wpm(void) {
  static uint32_t sample_timer = 0;
  if (timer_elapsed32(sample_timer) < WPM_SAMPLE_MS) return;
  sample_timer = timer_read32();
  memmove(wpm_history, wpm_history + 1, SCREEN_W - 1);
  wpm_history[SCREEN_W - 1] = get_current_wpm();
}

static void render_stats(bool restart) {
  static uint32_t draw_timer = 0;
  if (!restart && timer_elapsed32(draw_timer) < 250) return;
  draw_timer = timer_read32();

  char buf[12];
  uint32_t secs = timer_read32() / 1000;  // both halves are powered up together over USB
  write_row(5, "TIME");
  if (secs < 3600) {
    snprintf(buf, sizeof(buf), "%02lu:%02lu", secs / 60, secs % 60);
  } else if (secs < 100UL * 3600) {
    snprintf(buf, sizeof(buf), "%luh%02lu", secs / 3600, secs / 60 % 60);
  } else {
    snprintf(buf, sizeof(buf), "99h+");
  }
  write_row(6, buf);

  write_row(8, "KEYS");
  if (shared.keys < 100000) {
    snprintf(buf, sizeof(buf), "%5lu", shared.keys);
  } else {
    snprintf(buf, sizeof(buf), "%4luk", shared.keys / 1000);
  }
  write_row(9, buf);

  for (uint8_t x = 0; x < SCREEN_W; x++) {
    uint8_t wpm = wpm_history[x] > GRAPH_MAX_WPM ? GRAPH_MAX_WPM : wpm_history[x];
    uint8_t h = (uint16_t)wpm * GRAPH_H / GRAPH_MAX_WPM;
    for (uint8_t y = 0; y < GRAPH_H; y++) {
      bool baseline = y == GRAPH_H - 1;
      oled_write_pixel(x, GRAPH_TOP_Y + y, baseline || y >= GRAPH_H - h);
    }
  }
}

/* Mode: media - volume and the current track from the PC script.
   Uses the whole screen with text turned 90 degrees: a virtual 128x32 canvas whose lines run along
   the long side (read top to bottom, tops of the letters to the right), 4 lines of 21 characters. */

#define V_LINE_CHARS    21
#define V_STEP_MS       300   // horizontal scroll speed of long lines
#define V_HOLD_STEPS    5     // pause at both ends of a scrolling line
#define TEXT_SEPARATOR  0x1F  // between title and artist in shared.title

extern const unsigned char font[];  // the OLED font (OLED_FONT_H), same glyphs as the normal text

// u: 0..127 along a line, v: 0..31 across the lines
static void vpixel(uint8_t u, uint8_t v, bool on) {
  oled_write_pixel(SCREEN_W - 1 - v, u, on);
}

// exactly V_LINE_CHARS characters of `text` starting at `from`, padded with spaces
static void vline(uint8_t line, const char *text, uint8_t len, uint8_t from) {
  for (uint8_t i = 0; i < V_LINE_CHARS; i++) {
    uint8_t ch = from + i < len ? (uint8_t)text[from + i] : ' ';
    if (ch < OLED_FONT_START || ch > OLED_FONT_END) ch = ' ';
    const unsigned char *glyph = &font[(ch - OLED_FONT_START) * OLED_FONT_WIDTH];
    for (uint8_t k = 0; k < OLED_FONT_WIDTH; k++) {
      uint8_t bits = pgm_read_byte(glyph + k);
      for (uint8_t b = 0; b < 8; b++) {
        vpixel(i * OLED_FONT_WIDTH + k, line * 8 + b, bits >> b & 1);
      }
    }
  }
}

typedef struct {
  uint8_t pos;
  uint8_t len;
  uint8_t sum;  // cheap fingerprint: restart scrolling when the text changes
} vscroll_t;

// a line longer than the screen moves one character per step and starts over
static void vline_scroll(uint8_t line, const char *text, uint8_t len, vscroll_t *s, bool step) {
  uint8_t sum = 0;
  for (uint8_t i = 0; i < len; i++) sum += (uint8_t)text[i] * (i + 1);
  if (len != s->len || sum != s->sum) {
    s->pos = 0;
    s->len = len;
    s->sum = sum;
  }
  uint8_t from = 0;
  if (len > V_LINE_CHARS) {
    uint8_t travel = len - V_LINE_CHARS;
    if (step) s->pos = (s->pos + 1) % (travel + 2 * V_HOLD_STEPS + 1);
    from = s->pos < V_HOLD_STEPS ? 0 : s->pos - V_HOLD_STEPS;
    if (from > travel) from = travel;
  }
  vline(line, text, len, from);
}

static void render_media(bool restart) {
  static uint32_t draw_timer = 0;
  static vscroll_t title_scroll, artist_scroll;
  if (!restart && timer_elapsed32(draw_timer) < V_STEP_MS) return;
  draw_timer = timer_read32();

  char buf[V_LINE_CHARS + 1];
  if (!(shared.flags & MEDIA_FRESH)) {
    vline(0, "", 0, 0);
    vline(1, "  NO DATA FROM PC", 17, 0);
    vline(2, "  host/oled_feed.py", 19, 0);
    vline(3, "", 0, 0);
    return;
  }

  // line 0: state and volume
  const char *state = shared.title[0] == 0 ? "" : (shared.flags & MEDIA_PLAYING) ? "PLAY" : "PAUSE";
  if (shared.flags & MEDIA_MUTED) {
    snprintf(buf, sizeof(buf), "%-16s MUTE", state);
  } else {
    snprintf(buf, sizeof(buf), "%-13s VOL%3u%%", state, shared.volume);
  }
  vline(0, buf, strlen(buf), 0);

  // line 1: volume bar
  uint8_t fill = (uint16_t)shared.volume * 124 / 100;
  for (uint8_t u = 0; u < 126; u++) {
    for (uint8_t v = 8; v < 16; v++) {
      bool frame = (v == 9 || v == 14) || ((u == 0 || u == 125) && v > 9 && v < 14);
      bool inside = v > 9 && v < 14 && u >= 1 && u <= fill;
      vpixel(u, v, frame || inside);
    }
  }

  // lines 2-3: title and artist
  uint8_t len = strlen(shared.title);
  const char *sep = memchr(shared.title, TEXT_SEPARATOR, len);
  uint8_t title_len = sep ? sep - shared.title : len;
  const char *artist = sep ? sep + 1 : "";
  vline_scroll(2, shared.title, title_len, &title_scroll, !restart);
  vline_scroll(3, artist, strlen(artist), &artist_scroll, !restart);
}

bool oled_task_user(void) {
  if (is_keyboard_master()) {
    render_mods();
    return false;
  }

  sample_wpm();
#if OLED_TIMEOUT > 0
  // the animations redraw all the time and every redraw turns the screen back on,
  // so the timeout has to be checked here
  if (last_input_activity_elapsed() > OLED_TIMEOUT) {
    oled_off();
    return false;
  }
#endif

  static uint8_t shown_mode = 0xFF;
  bool restart = shared.mode != shown_mode;
  if (restart) {
    clear_rows(0, SCREEN_H / 8 - 1);  // media mode draws over the layer/WPM rows too
    shown_mode = shared.mode;
  }

  if (shared.mode != MODE_MEDIA) render_layer_wpm();
  switch (shared.mode) {
    case MODE_MAGE:  render_mage(restart); break;
    case MODE_LUNA:  render_luna(restart); break;
    case MODE_STATS: render_stats(restart); break;
    case MODE_MEDIA: render_media(restart); break;
  }
  return false;
}

#endif // OLED_ENABLE
