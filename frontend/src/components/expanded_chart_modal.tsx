import {
  Box,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Spinner,
  Stack,
  Text,
} from "@chakra-ui/react";
import React from "react";
import ReactEcharts from "echarts-for-react";

const ExpandedChartModal = (props: {
  isOpenExpandedChartModal: boolean;
  onCloseExpandedChartModal: () => void;
  EChartJSONspec: Record<any, any> | null;
  header: string;
}) => {
  return (
    <Modal
      size="6xl"
      isOpen={props.isOpenExpandedChartModal}
      onClose={props.onCloseExpandedChartModal}
    >
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>{props.header}</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Box
            my="1.5rem !important"
            width="100%"
            height="27rem"
            p="1rem"
            backgroundColor="white"
            borderRadius="1rem"
          >
            {props.EChartJSONspec ? (
              <ReactEcharts
                option={props.EChartJSONspec}
                style={{
                  height: "100%",
                  width: "100%",
                }}
              />
            ) : (
              <Stack alignItems="center" justifyContent="center" height="full">
                <Spinner />
                <Text>Loading...</Text>
              </Stack>
            )}
          </Box>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default ExpandedChartModal;
