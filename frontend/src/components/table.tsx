import * as React from "react";
import { Table, Thead, Tbody, Tr, Th, Td, chakra, Text, HStack, Badge } from "@chakra-ui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faSortDown,
    faSortUp
  } from "@fortawesome/free-solid-svg-icons";
import {
  useReactTable,
  flexRender,
  getCoreRowModel,
  ColumnDef,
  SortingState,
  getSortedRowModel
} from "@tanstack/react-table";

const getStatusColor = (status: string) => {
  switch(status){
    case "COMPLETE": {
      return "green"
    }
    case "RUNNING": {
      return "yellow"
    }
    case "ERROR": {
      return "red"
    }
  }
}

export type DataTableProps<Data extends object> = {
  data: Data[];
  columns: ColumnDef<Data, any>[];
  body_height?: string
};

export function DataTable<Data extends object>({
  data,
  columns,
  body_height
}: DataTableProps<Data>) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const table = useReactTable({
    columns,
    data,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    state: {
      sorting
    }
  });

  return (
    <Table>
      <Thead>
        {table.getHeaderGroups().map((headerGroup) => (
          <Tr backgroundColor="table.header_background" key={headerGroup.id}>
            {headerGroup.headers.map((header) => {
              // see https://tanstack.com/table/v8/docs/api/core/column-def#meta to type this correctly
              const meta: any = header.column.columnDef.meta;
              return (
                <Th
                  key={header.id}
                  onClick={header.column.getToggleSortingHandler()}
                  isNumeric={meta?.isNumeric}
                >
                    <HStack>
                        <Text color="table.font" fontSize="xs">
                        {flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                        )}
                        </Text>

                        <chakra.span pl="4">
                            {header.column.getIsSorted() ? (
                            header.column.getIsSorted() === "desc" ? (
                                <FontAwesomeIcon icon={faSortDown} />
                            ) : (
                                <FontAwesomeIcon icon={faSortUp} />
                            )
                            ) : null}
                        </chakra.span>
                    </HStack>
                </Th>
              );
            })}
          </Tr>
        ))}
      </Thead>
      <Tbody>
        {table.getRowModel().rows.map((row) => (
          <Tr height={body_height} key={row.id}>
            {row.getVisibleCells().map((cell) => {
              const meta: any = cell.column.columnDef.meta;
              return (
                <Td key={cell.id} isNumeric={meta?.isNumeric}>
                    {meta?.isBadge ?
                      <Badge borderRadius="35px" paddingInline="1rem" textTransform="lowercase" fontSize="sm" colorScheme={getStatusColor(String(cell.getValue()))}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </Badge>
                    : meta?.isButtons ?
                      flexRender(cell.column.columnDef.cell, cell.getContext())
                    :
                      <Text color="table.font" fontSize="sm" >{flexRender(cell.column.columnDef.cell, cell.getContext())}</Text>
                    }
                </Td>
              );
            })}
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
}
