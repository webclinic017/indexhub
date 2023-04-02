import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import reportWebVitals from "./reportWebVitals";
import { createStore, combineReducers, applyMiddleware } from "redux";
import createSagaMiddleware from "@redux-saga/core";
import { Provider } from "react-redux";
import reducer from "./store/reducer";
import mySaga from "./sagas/saga";
import { Auth0Provider } from "@auth0/auth0-react";

const sagaMiddleware = createSagaMiddleware();
const rootReducer = combineReducers({ reducer });
export type AppState = ReturnType<typeof rootReducer>;
const store = createStore(rootReducer, applyMiddleware(sagaMiddleware));
sagaMiddleware.run(mySaga);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const onAuth0RedirectCallback = (appState: any) => {
  window.location.assign(`${window.location.origin}${appState.returnTo}`);
};

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(
  <React.StrictMode>
    <Provider store={store}>
      <Auth0Provider
        domain={process.env.REACT_APP_AUTH0_DOMAIN!} // eslint-disable-line @typescript-eslint/no-non-null-assertion
        clientId={process.env.REACT_APP_CLIENT_ID!} // eslint-disable-line @typescript-eslint/no-non-null-assertion
        redirectUri={window.location.origin}
        audience={process.env.REACT_APP_INDEXHUB_API_AUDIENCE!} // eslint-disable-line @typescript-eslint/no-non-null-assertion
        onRedirectCallback={onAuth0RedirectCallback}
      >
        <App />
      </Auth0Provider>
    </Provider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
