import { extendTheme } from "@chakra-ui/react";

export const colors = {
  primary: {
    brand_colors: {
      main_blue: "#1b57f1",
      blue_2: "#194fdc",
      blue_3: "#14399a",
      blue_4: "#0e1d43",
      blue_5: "#4f4fff",
      off_grey: "#e2e2e2",
      not_black_black: "#0a0a0a",
      white: "#ffffff",
    },
  },
  supplementary: {
    indicators: {
      main_green: "#44aa7e",
      light_green: "#C6f6d5",
      green_2: "#2a9162",
      green_3: "#177548",
      main_red: "#9e2b2b",
      red_2: "#822020",
      red_3: "#14399a",
    },
    diverging_color: {
      main_yellow: "#b79320",
      yellow_2: "#a07712",
      yellow_3: "#6d4c09",
    },
    sister_colors: {
      main_purple: "#3b2599",
      purple_2: "#28197f",
      purple_3: "#1a0b5b",
      main_brown: "#b56321",
      brown_2: "#994c17",
      brown_3: "#7f3808",
      filter_grey: "#b7b7b7",
    },
  },
};

// Add themes in the same format with different color mappings (eg dark_theme, light_theme)
const default_theme = extendTheme({
  colors: {
    navbar: {
      background: colors.primary.brand_colors.white,
      icon: colors.primary.brand_colors.not_black_black,
      icon_highlight: colors.primary.brand_colors.blue_5,
      status_online: colors.supplementary.indicators.main_green,
      status_busy: colors.supplementary.indicators.main_red,
    },
    header: {
      background: colors.primary.brand_colors.white,
      text: colors.primary.brand_colors.not_black_black,
    },
    body: {
      background: colors.primary.brand_colors.white,
      header: colors.primary.brand_colors.not_black_black,
    },
    indicator: {
      main_green: colors.supplementary.indicators.main_green,
      light_green: colors.supplementary.indicators.light_green,
      green_2: colors.supplementary.indicators.green_2,
      green_3: colors.supplementary.indicators.green_3,
      main_red: colors.supplementary.indicators.main_red,
      red_2: colors.supplementary.indicators.red_2,
      red_3: colors.supplementary.indicators.red_3,
    },
    table: {
      header_background: "#f7fafc",
      font: "#4a5568",
      border: "#edf2f8",
    },
    steps: {
      active: colors.primary.brand_colors.blue_3,
      title: "#2d3748",
      subtitle: "#4a5568",
    },
    forms: {
      border: "#ecf0f3",
      bg_grey: "#f7fafc",
    },
    toasts: {
      success_bg: colors.supplementary.indicators.main_green,
      error_bg: colors.supplementary.indicators.main_red,
      info_bg: "#2b6cb0",
      subtitle: "#4a5568",
    },
    lists: {
      bg_grey: "#f7fafc",
      bg_light_grey: "#e4f0f9",
    },
  },
  fonts: {
    heading: `'Open Sans', sans-serif`,
    body: `'Raleway', sans-serif`,
  },
  styles: {
    global: () => ({
      "html, body": {
        fontSize: "md",
        fontWeight: "normal",
      },
    }),
  },
});

export const themes = {
  default_theme: default_theme,
};
