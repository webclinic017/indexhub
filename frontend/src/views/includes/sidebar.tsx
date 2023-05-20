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
} from '@chakra-ui/react'
import { ReactComponent as Logo } from "../../assets/images/svg/logo.svg";
import { useLocation, useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { AppState } from "../..";
import { useAuth0 } from "@auth0/auth0-react";
import { faBullseye, faDatabase, faChartLineUpDown } from "@fortawesome/pro-light-svg-icons";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'


interface NavButtonProps extends ButtonProps {
    icon: any
    label: string
}

export const NavButton = (props: NavButtonProps) => {
    const { icon, label, ...buttonProps } = props
    return (
        <Button variant="ghost" justifyContent="start" {...buttonProps}>
            <HStack spacing="2">
                <Box width="6"><FontAwesomeIcon size="lg" cursor="pointer" icon={icon}/></Box>
                <Text fontSize="sm">{label}</Text>
            </HStack>
        </Button>
    )
}


interface UserProfileProps {
    name: string
    image: string
    email: string
}

export const UserProfile = (props: UserProfileProps) => {
    const { name, image, email } = props
    return (
        <HStack spacing="3" p="1">
            <Avatar name={name} src={image} boxSize="9" />
            <Box overflow="hidden">
                <Text overflow="hidden" textOverflow="ellipsis" fontWeight="bold" fontSize="sm" textAlign="left">
                    {name}
                </Text>
                <Text className="ellipsis" color="muted" fontSize="sm" textAlign="left">
                    {email}
                </Text>
            </Box>
        </HStack>
    )
}


export const Sidebar = () => {
    const { user, logout, loginWithRedirect } = useAuth0();
    const navigate = useNavigate();
    const current_path = useLocation().pathname;
    const user_details = useSelector((state: AppState) => state.reducer?.user);

    return (
        <Stack p="1.5" minH="100vh" justify="space-between" spacing="1">
            <Stack shouldWrapChildren justify="start">
                <HStack m="5" mx="3"><Logo width="48" height="100%"/></HStack>
                <Stack>
                    <NavButton isActive={current_path.split("/")[1] == "trends"} label="Trends" icon={faChartLineUpDown} onClick={() => navigate("/trends")} />
                    <NavButton isActive={current_path.split("/")[1] == "objectives"} label="Objectives" icon={faBullseye} onClick={() => navigate("/objectives")} />
                    <NavButton isActive={current_path.split("/")[1] == "data"} label="Data" icon={faDatabase} onClick={() => navigate("/data")} />
                </Stack>
            </Stack>
            <Stack>
                <Divider />
                <Menu matchWidth>
                    <MenuButton cursor="pointer" borderRadius="5">
                        <UserProfile
                            name={user_details.nickname}
                            image=""
                            email={user_details.email}
                        />
                    </MenuButton>
                    <MenuList>
                        <MenuItem onClick={() => logout({ returnTo: window.location.origin })}>Logout</MenuItem>
                    </MenuList>
                </Menu>

            </Stack>
        </Stack>
    )
}