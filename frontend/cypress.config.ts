import { defineConfig } from "cypress";
declare const require: any; // eslint-disable-line @typescript-eslint/no-explicit-any
declare const process: any; // eslint-disable-line @typescript-eslint/no-explicit-any
require("dotenv").config();

export default defineConfig({
  e2e: {
    // setupNodeEvents(on, config) {
    //   // implement node event listeners here
    // },
    baseUrl: "http://localhost:3000",
    fixturesFolder: "tests/snapshots",
  },
  env: {
    auth0_username: process.env.AUTH0_USERNAME,
    auth0_password: process.env.AUTH0_PASSWORD,
    auth0_domain: process.env.REACT_APP_AUTH0_DOMAIN,
  },
});
