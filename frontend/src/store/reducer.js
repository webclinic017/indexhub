const initialState = {
  coming_soon: null,
  favourites: {
    items: [],
    itemsId: [],
  },
  user: {
    user_id: "",
    name: "",
    nickname: "",
    email: "",
    email_verified: false,
    report_ids: null,
  },
  report_ids: []
};

const reducer = (state = initialState, action) => {
  const newState = { ...state };

  switch (action.type) {
    case "LOAD_COMING_SOON_SUCCESS": {
      newState.coming_soon = action.coming_soon;
    }
  }
  switch (action.type) {
    case "ADD_FAVOURITES_SUCCESS": {
      const new_favourites = {};
      new_favourites.items = [...state.favourites.items, action.item];
      new_favourites.itemsId = [...state.favourites.itemsId, action.item.id];
      newState.favourites = new_favourites;
    }
  }
  switch (action.type) {
    case "ADD_REPORT_ID_SUCCESS": {
      newState.report_ids = [...state.report_ids, action.report_id]
    }
  }
  switch (action.type) {
    case "INIT_USER_SUCCESS": {
      newState.user = {
        user_id: action.user_details.user_id,
        name: action.user_details.name,
        nickname: action.user_details.nickname,
        email: action.user_details.email,
        email_verified: action.user_details.email_verified,
        report_ids: action.user_details.report_id,
      };
    }
  }
  return newState;
};

export default reducer;
