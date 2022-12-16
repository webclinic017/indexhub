//event types for listeners in saga middlewares
export const LOAD_COMING_SOON = "LOAD_COMING_SOON";
export const ADD_FAVOURITES = "ADD_FAVOURITES";
export const ADD_REPORT_ID = "ADD_REPORT_ID";

//event types for listeners in redux reducer
export const ADD_FAVOURITES_SUCCESS = "ADD_FAVOURITES_SUCCESS";
export const LOAD_COMING_SOON_SUCCESS = "LOAD_COMING_SOON_SUCCESS";
export const ADD_REPORT_ID_SUCCESS = "ADD_REPORT_ID_SUCCESS";

export const loadComingSoon = () => ({
  type: LOAD_COMING_SOON,
});

export const addToFavourites = (item) => ({
  type: ADD_FAVOURITES,
  item,
});

export const addReportId = (report_id, user_id) => ({
  type: ADD_REPORT_ID,
  report_id,
  user_id
});
