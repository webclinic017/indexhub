import React from "react";
import { Outlet } from "react-router-dom";
import { Grid, GridItem, VStack, Container } from "@chakra-ui/react";
import { Button } from '@chakra-ui/react'
import { ReactComponent as IndexHubLogo } from "../../assets/images/svg/indexhub_icon.svg";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faBell,
  faBook,
  faChevronRight,
  faDatabase,
  faFile,
  faGear,
  faMagnifyingGlass,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { Link, useLocation } from "react-router-dom"
import { useAuth0 } from "@auth0/auth0-react";

export default function Layout() {
  const {user, logout, loginWithRedirect} = useAuth0()
  const current_path = useLocation().pathname

  const getIconColor = (icon_path: string) => {
    if (current_path.split("/")[1] == icon_path){
      return "#4f4fff"
    }
    else return "white"
  }

  return (
    <>
      <Grid
        templateAreas={`"nav header"
                        "nav main"`}
        gridTemplateRows={"40px 1fr"}
        gridTemplateColumns={"100px 1fr"}
        h="100vh"
        fontWeight="bold"
      >
        <GridItem
          pl="2"
          bg="header.background"
          area={"header"}
          color="header.text"
          alignItems="center"
          display="flex"
        >
          <Container display="flex" justifyContent="flex-start" margin="unset" padding="unset">
            Header
          </Container>
          <Container display="flex" justifyContent="flex-end" margin="0 0 0 auto">
            {user?.sub ? (
              <Button colorScheme="teal" size="sm" onClick={() => logout({ returnTo: window.location.origin })}>
                Logout
              </Button>
            ) : (
              <Button colorScheme="teal" size="sm" onClick={() => loginWithRedirect({
                redirectUri: `http://localhost:3000${current_path}`
              })}>
                Login
              </Button>
            )}
          </Container>
        </GridItem>
        <GridItem
          pl="2"
          bg="navbar.background"
          area={"nav"}
          color="white"
          paddingLeft="unset"
        >
          <VStack
            justifyContent="space-between"
            alignItems="center"
            height="100vh"
          >
            <VStack
              padding="30px 0"
              height="50%"
              justifyContent="space-between"
            >
              <VStack>
                <Link to="/">
                <Container paddingBottom="20px">
                  <IndexHubLogo width="3rem" height="100%" />
                </Container>
                </Link>
                <Container
                  display="flex"
                  justifyContent="center"
                  alignItems="center"
                  backgroundColor="#333333"
                  width="3rem"
                  height="2rem"
                  borderRadius="5px"
                >
                  <FontAwesomeIcon icon={faMagnifyingGlass} />
                </Container>
              </VStack>
              <VStack>
                <Link to="/models">
                  <Container
                    display="flex"
                    justifyContent="center"
                    alignItems="center"
                    width="3rem"
                    height="3rem"
                  >
                    <FontAwesomeIcon icon={faDatabase} size="2x" color={getIconColor("models")}/>
                  </Container>
                </Link>
                <Link to="/reports">
                <Container
                  display="flex"
                  justifyContent="center"
                  alignItems="center"
                  width="3rem"
                  height="3rem"
                >
                  <FontAwesomeIcon icon={faFile} size="2x" color={getIconColor("reports")}/>
                </Container>
                </Link>
                <Link to="/notifications">
                <Container
                  display="flex"
                  justifyContent="center"
                  alignItems="center"
                  width="3rem"
                  height="3rem"
                >
                  <FontAwesomeIcon icon={faBell} size="2x" color={getIconColor("notifications")}/>
                </Container>
                </Link>
              </VStack>
              <VStack>
                <Container
                  display="flex"
                  justifyContent="center"
                  alignItems="center"
                  width="3rem"
                  height="3rem"
                >
                  <FontAwesomeIcon
                    icon={faChevronRight}
                    overlineThickness="bold"
                  />
                </Container>
              </VStack>
            </VStack>
            <VStack padding="30px" height="50%" justifyContent="flex-end">
              <Link to="/settings">
              <Container
                display="flex"
                justifyContent="center"
                alignItems="center"
                width="3rem"
                height="3rem"
              >
                <FontAwesomeIcon
                  icon={faGear}
                  overlineThickness="bold"
                  size="2x"
                  color={getIconColor("settings")}
                />
              </Container>
              </Link>
              <Link to="/docs">
              <Container
                display="flex"
                justifyContent="center"
                alignItems="center"
                width="3rem"
                height="3rem"
              >
                <FontAwesomeIcon
                  icon={faBook}
                  overlineThickness="bold"
                  size="2x"
                  color={getIconColor("docs")}
                />
              </Container>
              </Link>
              <Link to="/profile">
              <Container
                display="flex"
                justifyContent="center"
                alignItems="center"
                width="3rem"
                height="3rem"
              >
                <FontAwesomeIcon
                  icon={faUser}
                  overlineThickness="bold"
                  size="2x"
                  color={getIconColor("profile")}
                />
              </Container>
              </Link>
            </VStack>
          </VStack>
        </GridItem>
        <GridItem pl="2" bg="body.background" area={"main"}>
          <Outlet />
        </GridItem>
      </Grid>
    </>
  );
}
