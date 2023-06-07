declare namespace Cypress {
  // eslint-disable-next-line
  interface Chainable<Subject = any> {
    loginToAuth0(username: string, password: string): Chainable<any>;
  }
}
