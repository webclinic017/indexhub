import * as React from "react";
import { Table, Thead, Tbody, Tr, Th, Td, chakra, Text, HStack } from "@chakra-ui/react";
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

export type DataTableProps<Data extends object> = {
  data: Data[];
  columns: ColumnDef<Data, any>[];
};

export function DataTable<Data extends object>({
  data,
  columns
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
          <Tr backgroundColor="#f7fafc" key={headerGroup.id}>
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
                        <Text color="#4a5568" fontSize="12px" fontWeight="semibold">
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
          <Tr key={row.id}>
            {row.getVisibleCells().map((cell) => {
              // see https://tanstack.com/table/v8/docs/api/core/column-def#meta to type this correctly
              const meta: any = cell.column.columnDef.meta;
              return (
                <Td key={cell.id} isNumeric={meta?.isNumeric}>
                    <Text color="#4a5568" fontSize="0.9rem" fontWeight="normal">{flexRender(cell.column.columnDef.cell, cell.getContext())}</Text>
                </Td>
              );
            })}
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
}
