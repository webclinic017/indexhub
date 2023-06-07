import React from "react";
import {
  VStack,
  Text,
  TableContainer,
  Table,
  Thead,
  Tbody,
  Td,
  Tr,
} from "@chakra-ui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCheck } from "@fortawesome/pro-light-svg-icons";

type ListProps = {
  data: string[];
  title: string;
  subtitle: string;
  entity: string;
  state: Record<string, any[]>;
  stateSetter: (entity: string, value: any, is_multiple?: boolean) => void;
  minWidth?: string;
  maxWidth?: string;
};

export default function List({
  data,
  title,
  subtitle,
  entity,
  state,
  stateSetter,
  minWidth,
  maxWidth,
}: ListProps) {
  return (
    <VStack
      width="100%"
      maxWidth={maxWidth}
      minWidth={minWidth}
      height="19rem"
      alignItems="flex-start"
      border="1px solid #ecf0f3"
      padding="1rem"
    >
      <Text lineHeight="0.5" fontSize="sm" fontWeight="bold">
        {title}
      </Text>
      <Text
        width="100%"
        paddingBottom="0.5rem"
        borderBottom="1px solid #c6c9cc"
        fontSize="xs"
      >
        {subtitle}
      </Text>
      <TableContainer width="100%" backgroundColor="white" overflowY="scroll">
        <Table>
          <Thead backgroundColor="table.header_background"></Thead>
          <Tbody>
            {data.map((value: string, idx: number) => {
              return (
                <Tr
                  cursor="pointer"
                  key={idx}
                  onClick={() => {
                    stateSetter(entity, value);
                  }}
                >
                  <Td padding="unset" height="33px" fontSize="sm">
                    {idx + 1}
                  </Td>
                  <Td
                    padding="unset"
                    height="33px"
                    fontSize="sm"
                    textAlign="center"
                  >
                    {value}
                  </Td>
                  {state[entity].includes(value) ? (
                    <Td height="33px" padding="unset">
                      <FontAwesomeIcon icon={faCheck as any} />
                    </Td>
                  ) : (
                    <Td></Td>
                  )}
                </Tr>
              );
            })}
          </Tbody>
        </Table>
      </TableContainer>
    </VStack>
  );
}
