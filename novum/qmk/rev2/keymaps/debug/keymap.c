// Copyright 2024 Henri Nurmi <henri@nurmi.me>
// SPDX-License-Identifier: GPL-2.0-or-later

#include QMK_KEYBOARD_H

// clang-format off
enum layers {
    _DEFAULT = 0,
};

// The format follows the actual matrix, not the switch placement
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [_DEFAULT] = LAYOUT(
    KC_A, KC_B, KC_C, KC_D, KC_E, KC_F,    S(KC_F), S(KC_E), S(KC_D), S(KC_C), S(KC_B), S(KC_A),
    KC_G, KC_H, KC_I, KC_J, KC_K, KC_L,    S(KC_L), S(KC_K), S(KC_J), S(KC_I), S(KC_H), S(KC_G),
    KC_M, KC_N, KC_O, KC_P, KC_Q, KC_R,    S(KC_R), S(KC_Q), S(KC_P), S(KC_O), S(KC_N), S(KC_M),
    KC_S, KC_T, KC_U, KC_V, KC_W, KC_X,    S(KC_X), S(KC_W), S(KC_V), S(KC_U), S(KC_T), S(KC_S),
    KC_4, KC_Y, KC_Z, KC_1, KC_2, KC_3,    S(KC_3), S(KC_2), S(KC_1), S(KC_Z), S(KC_Y), S(KC_4)

    )
};
// clang-format on
