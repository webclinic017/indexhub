import React from 'react'
import { Box, BoxProps, Heading, HStack, Stack, Text } from '@chakra-ui/react'
import { faArrowTrendDown, faArrowTrendUp } from '@fortawesome/pro-light-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { colors } from '../theme/theme'

interface Props extends BoxProps {
  label: string
  value: string
  delta: {
    value: string
    isUpwardsTrend: boolean
  }
}
export const Stat = (props: Props) => {
  const { label, value, delta, ...boxProps } = props
  return (
    <Box px={{ base: '4', md: '6' }} py={{ base: '5', md: '6' }} {...boxProps}>
      <Stack>
        <HStack justify="space-between">
          <Text fontSize="sm" color="muted">
            {label}
          </Text>
          {/* <Icon as={FiMoreVertical} boxSize="5" color="muted" /> */}
        </HStack>
        <Stack spacing="4">
          <Heading size={{ base: 'sm', md: 'md' }}>{value}</Heading>
          <HStack spacing="1" fontWeight="medium">
            {/* <Icon
              color={delta.isUpwardsTrend ? 'success' : 'error'}
              as={delta.isUpwardsTrend ? FiArrowUpRight : FiArrowDownRight}
              boxSize="5"
            /> */}
            <FontAwesomeIcon
              color={delta.isUpwardsTrend ? colors.supplementary.indicators.main_green : colors.supplementary.indicators.main_red}
              icon={delta.isUpwardsTrend ? faArrowTrendUp as any : faArrowTrendDown as any}
            />
            <Text color={delta.isUpwardsTrend ? 'success' : 'error'}>{delta.value}</Text>
            <Text color="muted">vs last week</Text>
          </HStack>
        </Stack>
      </Stack>
    </Box>
  )
}