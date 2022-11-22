import { call, put, takeEvery } from "redux-saga/effects";
import axios from "axios";
import {
  ADD_FAVOURITES,
  ADD_FAVOURITES_SUCCESS,
  LOAD_COMING_SOON,
  LOAD_COMING_SOON_SUCCESS,
} from "../actions/actions";

function comingSoonApi() {
  return axios
    .get("https://imdb-api.com/en/API/ComingSoon/k_a6m0szqh")
    .then((response) => response.data);
}

function* workLoadComingSoon() {
  const coming_soon = yield call(comingSoonApi);
  yield put({ type: LOAD_COMING_SOON_SUCCESS, coming_soon });
}

function* workAddFavourites({ item }) {
  yield put({ type: ADD_FAVOURITES_SUCCESS, item });
}

function* mySaga() {
  yield takeEvery(LOAD_COMING_SOON, workLoadComingSoon);
  yield takeEvery(ADD_FAVOURITES, workAddFavourites);
}

export default mySaga;
