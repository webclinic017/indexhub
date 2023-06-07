import React from "react";
import {
  Avatar,
  Divider,
  HStack,
  Menu,
  Text,
  Box,
  Button,
  ButtonProps,
  MenuButton,
  MenuItem,
  MenuList,
  Stack,
} from "@chakra-ui/react";
import { ReactComponent as Logo } from "../../assets/images/svg/logo.svg";
import { useLocation, useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { AppState } from "../..";
import { useAuth0 } from "@auth0/auth0-react";
import {
  faBullseyeArrow,
  faDatabase,
  faChartLineUp,
} from "@fortawesome/pro-light-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

interface NavButtonProps extends ButtonProps {
  icon: any;
  label: string;
}

export const NavButton = (props: NavButtonProps) => {
  const { icon, label, ...buttonProps } = props;
  return (
    <Button variant="ghost" justifyContent="start" {...buttonProps}>
      <HStack spacing="2">
        <Box width="6">
          <FontAwesomeIcon size="lg" cursor="pointer" icon={icon} />
        </Box>
        <Text fontWeight="normal" fontSize="sm">
          {label}
        </Text>
      </HStack>
    </Button>
  );
};

interface UserProfileProps {
  name: string;
  image: string;
}

export const UserProfile = (props: UserProfileProps) => {
  const { name, image } = props;
  return (
    <HStack spacing="3" p="1">
      <Avatar name={name} src={image} boxSize="9" />
      <Box>
        <Text
          overflow="hidden"
          textOverflow="ellipsis"
          fontSize="sm"
          textAlign="left"
        >
          {name}
        </Text>
      </Box>
    </HStack>
  );
};

export const Sidebar = () => {
  const { logout } = useAuth0();
  const navigate = useNavigate();
  const current_path = useLocation().pathname;
  const user_details = useSelector((state: AppState) => state.reducer?.user);

  return (
    <Stack p="2" minH="100vh" justify="space-between">
      <Stack shouldWrapChildren justify="start">
        <HStack mx="3" my="6">
          <Logo width="48" height="100%" />
        </HStack>
        <Stack>
          <NavButton
            isActive={current_path.split("/")[1] == "trends"}
            label="Trends"
            icon={faChartLineUp}
            onClick={() => navigate("/")}
          />
          <NavButton
            isActive={current_path.split("/")[1] == "objectives"}
            label="Objectives"
            icon={faBullseyeArrow}
            onClick={() => navigate("/objectives")}
          />
          <NavButton
            isActive={current_path.split("/")[1] == "data"}
            label="Data"
            icon={faDatabase}
            onClick={() => navigate("/data")}
          />
        </Stack>
      </Stack>
      <Stack>
        <Divider />
        <Menu>
          <MenuButton cursor="pointer" borderRadius="5">
            <UserProfile name={user_details.name} image="" />
          </MenuButton>
          <MenuList>
            <MenuItem>
              <Text fontSize="sm" fontWeight="bold">
                {user_details.email}
              </Text>
            </MenuItem>
            <Divider />
            <MenuItem
              onClick={() => logout({ returnTo: window.location.origin })}
            >
              <Text fontSize="sm">Logout</Text>
            </MenuItem>
          </MenuList>
        </Menu>
      </Stack>
    </Stack>
  );
};
