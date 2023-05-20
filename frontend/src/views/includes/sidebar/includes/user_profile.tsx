import React from "react";
import { Avatar, Box, HStack, Text } from '@chakra-ui/react'

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