import React from "react";
import { Outlet } from "react-router-dom";
import { Grid, GridItem, VStack, Container, Text } from "@chakra-ui/react";
import { ReactComponent as IndexHubLogo } from "../../assets/images/svg/indexhub_icon.svg";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faBell,
  faBook,
  faChartLine,
  faDatabase,
  faGear,
  faRightFromBracket,
  faRightToBracket,
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
          <Container display="flex" justifyContent="flex-start" margin="unset" padding="unset"/>
          <Container display="flex" justifyContent="flex-end" margin="0 0 0 auto">
            {user?.sub ? (
              <FontAwesomeIcon cursor="pointer" icon={faRightFromBracket} onClick={() => logout({ returnTo: window.location.origin })}/>
            ) : (
              <FontAwesomeIcon cursor="pointer" icon={faRightToBracket} onClick={() => loginWithRedirect({
                redirectUri: `http://localhost:3000${current_path}`
              })}/>
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
              height="70%"
              justifyContent="space-between"
              width="100%"
            >
              <VStack>
                <Link to="/">
                <Container paddingBottom="20px">
                  <IndexHubLogo width="3rem" height="100%" />
                </Container>
                </Link>
              </VStack>
              <VStack width="100%">
                <Link style={{width:"100%"}} to="/models">
                  <Container
                    display="flex"
                    justifyContent="center"
                    alignItems="center"
                    flexDirection="column"
                    width="100%"
                    padding="1rem"
                  >
                    <FontAwesomeIcon icon={faDatabase} size="2x" color={getIconColor("models")}/>
                    <Text color={getIconColor("models")} fontSize="14px" marginTop="1rem">Models</Text>
                  </Container>
                </Link>
                <Link style={{width:"100%"}} to="/reports">
                <Container
                  display="flex"
                  justifyContent="center"
                  alignItems="center"
                  flexDirection="column"
                  width="100%"
                  padding="1rem"
                >
                  <FontAwesomeIcon icon={faChartLine} size="2x" color={getIconColor("reports")}/>
                  <Text color={getIconColor("reports")} fontSize="14px" marginTop="1rem">Reports</Text>
                </Container>
                </Link>
                <Link style={{width:"100%"}} to="/alerts">
                <Container
                  display="flex"
                  justifyContent="center"
                  alignItems="center"
                  flexDirection="column"
                  width="100%"
                  padding="1rem"
                >
                  <FontAwesomeIcon icon={faBell} size="2x" color={getIconColor("alerts")}/>
                  <Text color={getIconColor("alerts")} fontSize="14px" marginTop="1rem">Alerts</Text>
                </Container>
                </Link>
              </VStack>
            </VStack>
            <VStack padding="30px" height="50%" justifyContent="flex-end">
              <Link to="/settings">
              <Container
                display="flex"
                justifyContent="center"
                alignItems="center"
                width="100%"
                padding="1rem"
                flexDirection="column"
              >
                <FontAwesomeIcon
                  icon={faGear}
                  overlineThickness="bold"
                  size="2x"
                  color={getIconColor("settings")}
                />
                <Text color={getIconColor("settings")} fontSize="14px" marginTop="1rem">Settings</Text>
              </Container>
              </Link>
              <Link to="/docs">
              <Container
                display="flex"
                justifyContent="center"
                alignItems="center"
                width="100%"
                padding="1rem"
                flexDirection="column"
              >
                <FontAwesomeIcon
                  icon={faBook}
                  overlineThickness="bold"
                  size="2x"
                  color={getIconColor("docs")}
                />
                <Text color={getIconColor("docs")} fontSize="14px" marginTop="1rem">Docs</Text>
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
