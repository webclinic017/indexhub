import React from "react";
import { Outlet } from "react-router-dom";
import {
  Grid,
  GridItem,
  Container,
  Text,
  useDisclosure,
  Popover,
  PopoverTrigger,
  Button,
  PopoverContent,
  Stack,
  Link as ChakraLink,
  Box,
} from "@chakra-ui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useLocation } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { colors } from "../../theme/theme";
import Breadcrumbs from "../../components/breadcrumbs";
import { useNavigate } from "react-router-dom";
import { Sidebar } from "./sidebar/sidebar";
import { faChartLine, faDatabase, faPlusCircle } from "@fortawesome/pro-light-svg-icons";

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
      icon: faDatabase as any,
      onClick: () => navigate("/sources/new_source"),
    },
    {
      title: "Add Policy",
      description: "Add and configure a new Policy from your available Sources",
      icon: faChartLine as any,
      onClick: () => navigate("/policies/new_policy"),
    },
  ];

  return (
    <>
      <Grid
        templateAreas={`"nav header"
                        "nav main"`}
        gridTemplateRows={"100px 1fr"}
        gridTemplateColumns={"278.22px 1fr"}
        h="100vh"
      >
        <GridItem
          pl="2"
          bg="header.background"
          area={"header"}
          color="header.text"
          display="flex"
          flexDirection="column"
        >
          {/* Upper container */}
          <Container
            display="flex"
            alignItems="center"
            justifyContent="space-between"
            margin="0 0 0 auto"
            py="1rem"
            maxW="unset"
          >
            <Breadcrumbs current_path={current_path} />
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
                            <Box width="1rem">
                              <FontAwesomeIcon
                                size="lg"
                                cursor="pointer"
                                icon={item.icon}
                              />
                            </Box>
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
          </Container>
        </GridItem>
        <GridItem
          pl="2"
          bg="navbar.background"
          area={"nav"}
          paddingLeft="unset"
          fontWeight="bold"
        >
          <Sidebar />
        </GridItem>
        <GridItem pl="2" bg="body.background" area={"main"} overflowY="scroll">
          <Outlet />
        </GridItem>
      </Grid>
    </>
  );
}
