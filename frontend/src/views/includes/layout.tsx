import React from "react";
import { Outlet } from "react-router-dom";
import { Grid, GridItem } from "@chakra-ui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { colors } from "../../theme/theme";
import { Sidebar } from "./sidebar";
import { faPlusCircle } from "@fortawesome/pro-light-svg-icons";

export const PopoverIcon = (props: { isOpen: boolean }) => {
  const iconStyles = {
    color: props.isOpen
      ? colors.primary.brand_colors.main_blue
      : colors.primary.brand_colors.blue_3,
    transition: "color 0.2s",
  };
  return (
    <FontAwesomeIcon
      size="2x"
      cursor="pointer"
      icon={faPlusCircle as any}
      style={iconStyles}
    />
  );
};

export default function Layout() {
  return (
    <>
      <Grid
        templateAreas={`"nav main"`}
        gridTemplateColumns={"12rem 1fr"}
        h="100vh"
      >
        <GridItem bg="navbar.background" area="nav">
          <Sidebar />
        </GridItem>
        <GridItem p="8" bg="body.background" area={"main"} overflowY="scroll">
          <Outlet />
        </GridItem>
      </Grid>
    </>
  );
}
