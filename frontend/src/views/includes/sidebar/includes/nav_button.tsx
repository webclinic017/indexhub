import React from "react";
import { Box, Button, ButtonProps, HStack, Text } from '@chakra-ui/react'
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
                <Box width="6">
                    <FontAwesomeIcon size="lg" cursor="pointer" icon={icon}/>
                </Box>
                <Text fontSize="sm">{label}</Text>
            </HStack>
        </Button>
    )
}