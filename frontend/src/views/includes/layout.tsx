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
import {colors} from "../../theme/theme"
import Breadcrumbs from "../../components/breadcrumbs";

export default function Layout() {
  const {user, logout, loginWithRedirect} = useAuth0()
  const current_path = useLocation().pathname
  const getIconColor = (icon_path: string) => {
    if (current_path.split("/")[1] == icon_path){
      return colors.primary.brand_colors.blue_5
    }
    else return colors.primary.brand_colors.white
  }

  return (
    <>
      <Grid
        templateAreas={`"nav header"
                        "nav main"`}
        gridTemplateRows={"40px 1fr"}
        gridTemplateColumns={"100px 1fr"}
        h="100vh"
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
            <Breadcrumbs current_path={current_path}/>
          </Container>
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
          fontWeight="bold"
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
                    <FontAwesomeIcon style={{transition:"color 0.3s ease-out"}} icon={faDatabase} size="2x" color={getIconColor("models")}/>
                    <Text transition="color 0.3s ease-out" color={getIconColor("models")} fontSize="sm" marginTop="1rem">Models</Text>
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
                  <FontAwesomeIcon style={{transition:"color 0.3s ease-out"}} icon={faChartLine} size="2x" color={getIconColor("reports")}/>
                  <Text transition="color 0.3s ease-out" color={getIconColor("reports")} fontSize="sm" marginTop="1rem">Reports</Text>
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
                  <FontAwesomeIcon style={{transition:"color 0.3s ease-out"}} icon={faBell} size="2x" color={getIconColor("alerts")}/>
                  <Text transition="color 0.3s ease-out" color={getIconColor("alerts")} fontSize="sm" marginTop="1rem">Alerts</Text>
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
                  style={{transition:"color 0.3s ease-out"}}
                />
                <Text transition="color 0.3s ease-out" color={getIconColor("settings")} fontSize="sm" marginTop="1rem">Settings</Text>
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
                  style={{transition:"color 0.3s ease-out"}}
                />
                <Text transition="color 0.3s ease-out" color={getIconColor("docs")} fontSize="sm" marginTop="1rem">Docs</Text>
              </Container>
              </Link>
            </VStack>
          </VStack>
        </GridItem>
        <GridItem pl="2" bg="body.background" area={"main"} overflowY="scroll">
          <Outlet />
        </GridItem>
      </Grid>
    </>
  );
}
