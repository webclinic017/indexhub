import React from "react";
import { render, screen } from "@testing-library/react";
import App from "./App";

import { Provider } from "react-redux";
import configureStore from "redux-mock-store";

describe("With React Testing Library", () => {
  const initialState = { output: 10 };
  const mockStore = configureStore();
  let stores;

  it('Shows "Hello world!"', () => {
    stores = mockStore(initialState);

    render(
      <Provider store={stores}>
        <App />
      </Provider>
    );

    const linkElement = screen.getByText(/home/i);
    expect(linkElement).toBeInTheDocument();
  });
});
