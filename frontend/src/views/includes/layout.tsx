import React from "react";
import { Outlet } from "react-router-dom";
import { Grid, GridItem, VStack, Container } from "@chakra-ui/react";
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

export default function Layout() {
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
          Header
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
            height="100%"
          >
            <VStack
              padding="30px 0"
              height="50%"
              justifyContent="space-between"
            >
              <VStack>
                <Container paddingBottom="20px">
                  <IndexHubLogo width="3rem" height="100%" />
                </Container>
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
                <Container
                  display="flex"
                  justifyContent="center"
                  alignItems="center"
                  width="3rem"
                  height="3rem"
                >
                  <FontAwesomeIcon icon={faDatabase} size="2x" />
                </Container>
                <Container
                  display="flex"
                  justifyContent="center"
                  alignItems="center"
                  width="3rem"
                  height="3rem"
                >
                  <FontAwesomeIcon icon={faFile} size="2x" />
                </Container>
                <Container
                  display="flex"
                  justifyContent="center"
                  alignItems="center"
                  width="3rem"
                  height="3rem"
                >
                  <FontAwesomeIcon icon={faBell} size="2x" />
                </Container>
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
                />
              </Container>
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
                />
              </Container>
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
                />
              </Container>
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
