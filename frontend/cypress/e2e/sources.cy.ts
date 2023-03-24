import * as cypress from "cypress"; // eslint-disable-line @typescript-eslint/no-unused-vars

describe("Test Sources", () => {
  beforeEach(() => {
    cy.loginToAuth0(
      Cypress.env("auth0_username"),
      Cypress.env("auth0_password")
    );
    cy.visit("/sources");
  });

  it("load sources page", () => {
    cy.visit("/sources");
  });

  it("create new source (all source credentials available)", () => {
    cy.visit("/sources/new_source");
    cy.intercept("GET", "/sources/schema/*", {
      fixture: "sources/sources_schema_all_credentials_available.json",
    }).as("mockedSourcesSchema");
    cy.contains("Needs Credentials").should("not.exist");
  });

  it("create new source (all source credentials not available)", () => {
    cy.visit("/sources/new_source");
    cy.intercept("GET", "/sources/schema/*", {
      fixture: "sources/sources_schema_all_credentials_not_available.json",
    }).as("mockedSourcesSchema");
    cy.contains("Needs Credentials").should("exist");
  });
});
