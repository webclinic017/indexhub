import React from "react"
import { Box, Flex, Center, Stack, Text} from '@chakra-ui/react'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCheckCircle, faXmarkCircle, IconDefinition } from "@fortawesome/free-regular-svg-icons";
import { faCircleExclamation } from "@fortawesome/free-solid-svg-icons";

const toast_colors: Record<string, string> = {
    "success": "toasts.success_bg",
    "error": "toasts.error_bg",
    "info": "toasts.info_bg"
}

const toast_icons: Record<string, IconDefinition> = {
    "success": faCheckCircle,
    "error": faXmarkCircle,
    "info": faCircleExclamation
}

const PrimaryToast = (props: { title: string, subtitle: string , type: string, toast: any}) => {
    return (
        <Box
            as="section"
        >
            <Flex direction="row-reverse">
            <Flex
                direction={{ base: 'column', sm: 'row' }}
                width={{ base: 'full', sm: 'md' }}
                boxShadow="md"
                bg="white"
                borderRadius="lg"
                overflow="hidden"
            >
                <Center display={{ base: 'none', sm: 'flex' }} bg={toast_colors[props.type]} px="5">
                <FontAwesomeIcon icon={toast_icons[props.type]} color="white" size="2x" />
                </Center>
                <Stack direction="row" p="4" spacing="3" flex="1">
                    <Stack spacing="2.5" flex="1">
                        <Stack spacing="1">
                        <Text fontSize="sm" fontWeight="bold">
                            {props.title}
                        </Text>
                        <Text fontSize="sm" color="toats.subtitle">
                            {props.subtitle}
                        </Text>
                        </Stack>
                    </Stack>
                    {/* To be added in the future
                    <CloseButton onClick={() => props.toast.closeAll()} transform="translateY(-6px)" /> */}
                </Stack>
            </Flex>
            </Flex>
        </Box>
    )
}

const Toast = (toast: any, title = "", subtitle = "", type: string, position = "top-right") => {
    toast({
        position: position,
        render: () => (
            <PrimaryToast title={title} subtitle={subtitle} type={type} toast={toast}/>
        ),
    })
}

export default Toast