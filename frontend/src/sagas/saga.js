import { call, put, takeEvery } from "redux-saga/effects";
import axios from "axios";
import {
  ADD_FAVOURITES,
  ADD_FAVOURITES_SUCCESS,
  ADD_REPORT_ID_SUCCESS,
  INIT_USER_SUCCESS,
  LOAD_COMING_SOON,
  LOAD_COMING_SOON_SUCCESS,
  ADD_REPORT_ID,
  INIT_USER

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

function* workAddReportId({ report_id, user_id }) {
  yield put({ type: ADD_REPORT_ID_SUCCESS, report_id, user_id });
}

function* workInitUser({user_details}) {
  yield put({ type: INIT_USER_SUCCESS, user_details });
}

function* mySaga() {
  yield takeEvery(LOAD_COMING_SOON, workLoadComingSoon);
  yield takeEvery(ADD_FAVOURITES, workAddFavourites);
  yield takeEvery(ADD_REPORT_ID, workAddReportId);
  yield takeEvery(INIT_USER, workInitUser)
}

export default mySaga;
