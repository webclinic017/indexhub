import React from "react";
import { Outlet } from "react-router-dom";
import {
  Grid,
  GridItem,
  VStack,
  Container,
  Text,
  useDisclosure,
  Popover,
  PopoverTrigger,
  Button,
  PopoverContent,
  Stack,
  Link as ChakraLink,
} from "@chakra-ui/react";
import { ReactComponent as IndexHubLogo } from "../../assets/images/svg/indexhub_icon.svg";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faBell,
  faBook,
  faChartLine,
  faDatabase,
  faGear,
  faPlusCircle,
  faRightFromBracket,
  faRightToBracket,
} from "@fortawesome/free-solid-svg-icons";
import { Link, useLocation } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { colors } from "../../theme/theme";
import Breadcrumbs from "../../components/breadcrumbs";
import { useNavigate } from "react-router-dom";

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
      icon={faPlusCircle}
      style={iconStyles}
    />
  );
};

export default function Layout() {
  const { user, logout, loginWithRedirect } = useAuth0();
  const current_path = useLocation().pathname;
  const { isOpen, onClose, onOpen } = useDisclosure({ defaultIsOpen: false });
  const navigate = useNavigate();

  const getIconColor = (icon_path: string) => {
    if (current_path.split("/")[1] == icon_path) {
      return colors.primary.brand_colors.blue_5;
    } else return colors.primary.brand_colors.not_black_black;
  };

  const add_source_reports_items = [
    {
      title: "Add Source",
      description: "Add and configure a new Source to generate reports from",
      icon: faDatabase,
      onClick: () => navigate("/sources/new_source"),
    },
    {
      title: "Add Policy",
      description: "Add and configure a new Policy from your available Sources",
      icon: faChartLine,
      onClick: () => navigate("/policies/new_policy"),
    },
  ];

  return (
    <>
      <Grid
        templateAreas={`"nav header"
                        "nav main"`}
        gridTemplateRows={"100px 1fr"}
        gridTemplateColumns={"100px 1fr"}
        h="100vh"
      >
        <GridItem
          pl="2"
          bg="header.background"
          area={"header"}
          color="header.text"
          // alignItems="center"
          display="flex"
          flexDirection="column"
        >
          {/* Upper container */}
          <Container
            display="flex"
            alignItems="center"
            justifyContent="flex-end"
            margin="0 0 0 auto"
            py="1rem"
          >
            <Popover
              trigger="hover"
              onClose={onClose}
              onOpen={onOpen}
              isOpen={isOpen}
              placement="bottom"
              gutter={12}
            >
              {({ isOpen }) => (
                <>
                  <PopoverTrigger>
                    <Button
                      _hover={{ textDecoration: "none" }}
                      variant="link"
                      rightIcon={<PopoverIcon isOpen={isOpen} />}
                      marginRight="1rem"
                    />
                  </PopoverTrigger>
                  <PopoverContent width="sm" p="5">
                    <Stack textDecoration="none">
                      {add_source_reports_items.map((item, id) => (
                        <ChakraLink
                          _hover={{
                            textDecoration: "none",
                            backgroundColor: "#f8fafc",
                          }}
                          variant="menu"
                          key={id}
                          borderRadius="0.5rem"
                          onClick={item.onClick}
                        >
                          <Stack spacing="4" direction="row" p="3">
                            <FontAwesomeIcon
                              size="lg"
                              cursor="pointer"
                              icon={item.icon}
                            />
                            <Stack spacing="1">
                              <Text fontWeight="bold">{item.title}</Text>
                              <Text fontSize="sm" color="muted">
                                {item.description}
                              </Text>
                            </Stack>
                          </Stack>
                        </ChakraLink>
                      ))}
                    </Stack>
                  </PopoverContent>
                </>
              )}
            </Popover>
            {user?.sub ? (
              <FontAwesomeIcon
                cursor="pointer"
                icon={faRightFromBracket}
                onClick={() => logout({ returnTo: window.location.origin })}
              />
            ) : (
              <FontAwesomeIcon
                cursor="pointer"
                icon={faRightToBracket}
                onClick={() =>
                  loginWithRedirect({
                    appState: { returnTo: current_path },
                  })
                }
              />
            )}
          </Container>

          {/* Lower container */}
          <Container
            display="flex"
            justifyContent="flex-start"
            margin="unset"
            padding="unset"
          >
            <Breadcrumbs current_path={current_path} />
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
                <Link style={{ width: "100%" }} to="/sources">
                  <Container
                    display="flex"
                    justifyContent="center"
                    alignItems="center"
                    flexDirection="column"
                    width="100%"
                    padding="1rem"
                  >
                    <FontAwesomeIcon
                      style={{ transition: "color 0.3s ease-out" }}
                      icon={faDatabase}
                      size="lg"
                      color={getIconColor("sources")}
                    />
                    <Text
                      transition="color 0.3s ease-out"
                      color={getIconColor("sources")}
                      fontSize="sm"
                      marginTop="0.5rem"
                    >
                      Sources
                    </Text>
                  </Container>
                </Link>
                <Link style={{ width: "100%" }} to="/reports">
                  <Container
                    display="flex"
                    justifyContent="center"
                    alignItems="center"
                    flexDirection="column"
                    width="100%"
                    padding="1rem"
                  >
                    <FontAwesomeIcon
                      style={{ transition: "color 0.3s ease-out" }}
                      icon={faChartLine}
                      size="lg"
                      color={getIconColor("reports")}
                    />
                    <Text
                      transition="color 0.3s ease-out"
                      color={getIconColor("reports")}
                      fontSize="sm"
                      marginTop="0.5rem"
                    >
                      Reports
                    </Text>
                  </Container>
                </Link>
                <Link style={{ width: "100%" }} to="/alerts">
                  <Container
                    display="flex"
                    justifyContent="center"
                    alignItems="center"
                    flexDirection="column"
                    width="100%"
                    padding="1rem"
                  >
                    <FontAwesomeIcon
                      style={{ transition: "color 0.3s ease-out" }}
                      icon={faBell}
                      size="lg"
                      color={getIconColor("alerts")}
                    />
                    <Text
                      transition="color 0.3s ease-out"
                      color={getIconColor("alerts")}
                      fontSize="sm"
                      marginTop="0.5rem"
                    >
                      Alerts
                    </Text>
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
                    size="lg"
                    color={getIconColor("settings")}
                    style={{ transition: "color 0.3s ease-out" }}
                  />
                  <Text
                    transition="color 0.3s ease-out"
                    color={getIconColor("settings")}
                    fontSize="sm"
                    marginTop="0.5rem"
                  >
                    Settings
                  </Text>
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
                    size="lg"
                    color={getIconColor("docs")}
                    style={{ transition: "color 0.3s ease-out" }}
                  />
                  <Text
                    transition="color 0.3s ease-out"
                    color={getIconColor("docs")}
                    fontSize="sm"
                    marginTop="0.5rem"
                  >
                    Docs
                  </Text>
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
