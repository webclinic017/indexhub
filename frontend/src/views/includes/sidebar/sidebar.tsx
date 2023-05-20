import React from "react";
import {
    Divider,
    Flex,
    Menu,
    MenuButton,
    MenuItem,
    MenuList,
    Stack,
} from '@chakra-ui/react'
import { ReactComponent as IndexHubLogo } from "../../../assets/images/svg/indexhub_icon.svg";
import { NavButton } from './includes/nav_button'
import { UserProfile } from './includes/user_profile'
import { useLocation, useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { AppState } from "../../..";
import { useAuth0 } from "@auth0/auth0-react";
import { faBullseye, faDatabase, faChartLineUpDown } from "@fortawesome/pro-light-svg-icons";


export const Sidebar = () => {
    const { user, logout, loginWithRedirect } = useAuth0();
    const navigate = useNavigate();
    const current_path = useLocation().pathname;
    const user_details = useSelector((state: AppState) => state.reducer?.user);

    return (
        <Stack p="1" minH="100vh" justify="space-between" spacing="1">
            <Stack shouldWrapChildren justify="start">
                <Stack m="6" mx="2"><IndexHubLogo width="48" height="100%"/></Stack>
                <Stack mt="3">
                    <NavButton isActive={current_path.split("/")[1] == "trends"} label="Trends" icon={faChartLineUpDown} onClick={() => navigate("/trends")} />
                    <NavButton isActive={current_path.split("/")[1] == "objectives"} label="Objectives" icon={faBullseye} onClick={() => navigate("/objectives")} />
                    <NavButton isActive={current_path.split("/")[1] == "data"} label="Data" icon={faDatabase} onClick={() => navigate("/data")} />
                </Stack>
            </Stack>
            <Stack spacing="4">
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