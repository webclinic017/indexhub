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
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
} from "@chakra-ui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useLocation } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { colors } from "../../theme/theme";
import Breadcrumbs from "../../components/breadcrumbs";
import { useNavigate } from "react-router-dom";
import { Sidebar } from "./sidebar";
import { faChartLine, faDatabase, faPlusCircle } from "@fortawesome/pro-light-svg-icons";
import NewSource from "../sources/new_source";

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
  const current_path = useLocation().pathname;
  const { isOpen, onClose, onOpen } = useDisclosure({ defaultIsOpen: false });
  const navigate = useNavigate();

  const {
    isOpen: isOpenNewSourceModal,
    onOpen: onOpenNewSourceModal,
    onClose: onCloseNewSourceModal
  } = useDisclosure()

  const add_source_reports_items = [
    {
      title: "Add Source",
      description: "Connect to a data source",
      icon: faDatabase as any,
      onClick: () => onOpenNewSourceModal(),
    },
    {
      title: "Add Objective",
      description: "Create new forecasting objective",
      icon: faChartLine as any,
      onClick: () => navigate("/objectives/new_objective"),
    },
  ];

  return (
    <>
      <Grid
        templateAreas={`"nav header" "nav main"`}
        gridTemplateRows={"70px 1fr"}
        gridTemplateColumns={"11rem 1fr"}
        h="100vh"
      >
        <GridItem
          m="2"
          mt="4"
          bg="header.background"
          area={"header"}
          color="header.text"
          display="flex"
          flexDirection="column"
        >
          <Container
            display="flex"
            alignItems="center"
            justifyContent="space-between"
            margin="0 0 0 auto"
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
                            backgroundColor: "colors.primary.brand_colors.gray",
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
        <GridItem bg="navbar.background" area="nav"><Sidebar /></GridItem>
        <GridItem px="3" bg="body.background" area={"main"} overflowY="scroll">
          <Outlet />
        </GridItem>
      </Grid>
      <Modal size="6xl" isOpen={isOpenNewSourceModal} onClose={onCloseNewSourceModal}>
        <ModalOverlay />
        <ModalContent>
          <ModalCloseButton />
          <ModalBody>
            <NewSource />
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
}
