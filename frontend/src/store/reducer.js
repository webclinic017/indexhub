const initialState = {
  coming_soon: null,
  favourites: {
    items: [],
    itemsId: [],
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
  return newState;
};

export default reducer;
