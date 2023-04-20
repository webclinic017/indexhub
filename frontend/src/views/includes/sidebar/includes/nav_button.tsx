import React from "react";
import { As, Box, Button, ButtonProps, HStack, Icon, Text } from '@chakra-ui/react'
import { IconDefinition } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'



interface NavButtonProps extends ButtonProps {
    icon: any
    label: string
}

export const NavButton = (props: NavButtonProps) => {
    const { icon, label, ...buttonProps } = props
    return (
        <Button variant="ghost" justifyContent="start" {...buttonProps}>
            <HStack spacing="3">
                <Box width="2rem">
                    <FontAwesomeIcon
                        size="lg"
                        cursor="pointer"
                        icon={icon}
                    />
                </Box>
                <Text>{label}</Text>
            </HStack>
        </Button>
    )
}