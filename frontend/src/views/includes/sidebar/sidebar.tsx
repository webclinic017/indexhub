import React from "react";
import {
    Box,
    Button,
    Divider,
    Flex,
    HStack,
    Menu,
    MenuButton,
    MenuItem,
    MenuList,
    Popover,
    PopoverArrow,
    PopoverBody,
    PopoverCloseButton,
    PopoverContent,
    PopoverHeader,
    PopoverTrigger,
    Progress,
    Stack,
    Text
} from '@chakra-ui/react'
import { ReactComponent as IndexHubLogo } from "../../../assets/images/svg/indexhub_icon.svg";
import { NavButton } from './includes/nav_button'
import { UserProfile } from './includes/user_profile'
import { useLocation, useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { AppState } from "../../..";
import { useAuth0 } from "@auth0/auth0-react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBell, faBullseyeArrow, faDatabase, faHouse } from "@fortawesome/pro-light-svg-icons";


export const Sidebar = () => {
    const { user, logout, loginWithRedirect } = useAuth0();
    const navigate = useNavigate();
    const current_path = useLocation().pathname;
    const user_details = useSelector((state: AppState) => state.reducer?.user);

    return (
        <Flex as="section" minH="100vh" bg="bg-canvas">
            <Flex
                flex="1"
                bg="bg-surface"
                boxShadow="sm"
                maxW={{ base: 'full', sm: 'xs' }}
                py={{ base: '6', sm: '8' }}
                px={{ base: '4', sm: '6' }}
            >
                <Stack justify="space-between" spacing="1">
                    <Stack spacing={{ base: '5', sm: '6' }} shouldWrapChildren height="37vh" justify="space-between">
                        {/* <Stack alignItems="center"> */}
                        <IndexHubLogo width="3rem" height="100%" />
                        {/* </Stack> */}

                        {/* <InputGroup>
                            <InputLeftElement pointerEvents="none">
                                <Icon as={FiSearch} color="muted" boxSize="5" />
                            </InputLeftElement>
                            <Input placeholder="Search" />
                        </InputGroup> */}
                        <Stack spacing="4">
                            <NavButton isActive={current_path.split("/")[1] == "dashboard"} label="Dashboard" icon={faHouse} onClick={() => navigate("/dashboard")} />
                            <NavButton isActive={current_path.split("/")[1] == "sources"} label="Sources" icon={faDatabase} onClick={() => navigate("/sources")} />
                            <NavButton isActive={current_path.split("/")[1] == "policies"} label="Policies" icon={faBullseyeArrow} onClick={() => navigate("/policies")} />
                            <Popover isLazy placement="right">
                                <PopoverTrigger>
                                    <Button variant="ghost" justifyContent="start">
                                        <HStack spacing="3">
                                            <Box width="2rem">
                                                <FontAwesomeIcon
                                                    size="lg"
                                                    cursor="pointer"
                                                    icon={faBell as any}
                                                />
                                            </Box>
                                            <Text>Alerts</Text>
                                        </HStack>
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent>
                                    <PopoverHeader fontWeight='semibold'>Alerts</PopoverHeader>
                                    <PopoverArrow />
                                    <PopoverCloseButton />
                                    <PopoverBody py="5rem">
                                        <Stack alignItems="center">
                                            <Text>Alerts will appear here</Text>
                                        </Stack>

                                    </PopoverBody>
                                </PopoverContent>
                            </Popover>
                            {/* <NavButton label="Alerts" icon={faBell} /> */}
                            {/* <NavButton label="Users" icon={faBell} /> */}
                        </Stack>
                    </Stack>
                    <Stack spacing={{ base: '5', sm: '6' }}>
                        {/* <Stack spacing="1">
                            <NavButton label="Help" icon={faBell} />
                            <NavButton label="Settings" icon={faBell} />
                        </Stack> */}
                        <Box bg="bg-subtle" px="4" py="5" borderRadius="lg">
                            <Stack spacing="4">
                                <Stack spacing="1">
                                    <Text fontSize="sm" fontWeight="medium">
                                        Almost there
                                    </Text>
                                    <Text fontSize="sm" color="muted">
                                        Fill in some more information about you and your person.
                                    </Text>
                                </Stack>
                                <Progress value={80} size="sm" aria-label="Profile Update Progress" />
                                <HStack spacing="3">
                                    <Button variant="link" size="sm">
                                        Dismiss
                                    </Button>
                                    <Button variant="link" size="sm" colorScheme="blue">
                                        Update profile
                                    </Button>
                                </HStack>
                            </Stack>
                        </Box>
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
            </Flex>
        </Flex>
    )
}