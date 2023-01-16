import { extendTheme } from "@chakra-ui/react";

// Add themes in the same format with different color mappings (eg dark_theme, light_theme)
const default_theme = extendTheme({
  colors: {
    navbar: {
      background: "#0a0a0a",
      icon: "#e2e2e2",
      icon_highlight: "#1B57F1",
      status_online: "#44aa7e",
      status_busy: "#9e2b2b",
    },
    header: {
      background: "#e2e2e2",
      text: "#0a0a0a",
    },
    body: {
      background: "#ffffff",
      header: "#0a0a0a",
    },
  },
  fonts: {
    heading: `'Open Sans', sans-serif`,
    body: `'Raleway', sans-serif`,
  },
  styles: {
    global: (props: any) => ({
      'html, body': {
        fontSize: "md",
        fontWeight: "normal"
      },
    }),
  },
});

const themes = {
  default_theme: default_theme,
};

export default themes;
