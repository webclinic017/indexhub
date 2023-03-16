const initialState = {
  coming_soon: null,
  favourites: {
    items: [],
    itemsId: [],
  },
  user: {
    id: "",
    name: "",
    nickname: "",
    email: "",
    email_verified: false,
    has_s3_creds: false,
    has_azure_creds: false,
    storage_tag: "",
    storage_bucket_name: "",
    storage_created_at: "",
  },
  report_ids: [],
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
      newState.report_ids = [...state.report_ids, action.report_id];
    }
  }
  switch (action.type) {
    case "INIT_USER_SUCCESS": {
      newState.user = action.user_details;
    }
  }
  return newState;
};

export default reducer;
