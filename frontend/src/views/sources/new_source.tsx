import React, { useEffect, useState } from "react";
import {
  Container,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  useDisclosure,
} from "@chakra-ui/react";
import { useStep } from "../../utilities/hooks/useStep";
import { Step } from "../../components/step";
import SourcePath from "./steps/source_path";
import ConfigureSource from "./steps/configure_source";
import { useToast } from "@chakra-ui/react";
import Toast from "../../components/toast";
import ConfirmCreateSource from "./steps/confirm_create_source";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import {
  createSource as createSourceApi,
  getSourcesSchema,
  getS3SourceColumns,
} from "../../utilities/backend_calls/source";
import { useSelector } from "react-redux";
import { AppState } from "../../index";
import { useNavigate } from "react-router-dom";
import SourceType from "./steps/source_type";
import SourceCredentials from "./source_credentials";
import { createCredentials } from "../../utilities/backend_calls/credentials";

const steps = [
  {
    title: "Step 1",
    description: "Your source type",
  },
  {
    title: "Step 2",
    description: "Your source destination",
  },
  {
    title: "Step 3",
    description: "Configure your dataset",
  },
  {
    title: "Step 4",
    description: "Confirm source creation",
  },
];

export default function NewSource() {
  const [sources_schema, setSourcesSchema] = useState<Record<any, any>>({}); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [source_type, setSourceType] = useState("");
  const [source_configs, setSourceConfigs] = useState<Record<string, string>>(
    {}
  );
  const [source_columns, setSourceColumns] = useState([""]);
  const [column_options, setColumnOptions] = useState([""]);
  const [time_col, setTimeCol] = useState("");
  const [freq, setFreq] = useState("d");
  const [entity_cols, setEntityCols] = useState<string[]>([]);
  const [feature_cols, setFeatureCols] = useState<string[]>([]);
  const [currentStep, { goToNextStep, goToPrevStep }] = useStep({
    maxStep: steps.length,
  });
  const access_token_indexhub_api = useAuth0AccessToken();

  const toast = useToast();
  const navigate = useNavigate();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const user_details = useSelector((state: AppState) => state.reducer?.user);

  useEffect(() => {
    const getSourcesSchemaApi = async () => {
      const sources_schema = await getSourcesSchema(
        user_details.id,
        access_token_indexhub_api
      );
      setSourcesSchema(sources_schema);
    };
    if (access_token_indexhub_api && user_details.id) {
      getSourcesSchemaApi();
    }
  }, [access_token_indexhub_api, user_details]);

  useEffect(() => {
    setColumnOptions(source_columns);
  }, [source_columns]);

  useEffect(() => {
    let selected_columns: string[] = entity_cols.concat([]);
    selected_columns.push(time_col);
    selected_columns = selected_columns.filter((val) => {
      return val != "";
    });

    const optionsToRemove = new Set(selected_columns);

    const new_options = source_columns.filter((col) => {
      return !optionsToRemove.has(col);
    });

    setColumnOptions(new_options);
    setFeatureCols(new_options);
  }, [time_col, entity_cols]);

  const submitSourceType = (source_type: string) => {
    setSourceType(source_type);
    if (sources_schema[source_type]["is_authenticated"]) {
      goToNextStep();
    } else {
      onOpen();
    }
  };

  const submitSourceCreds = async (source_creds: Record<string, string>) => {
    const response = await createCredentials(
      source_creds,
      source_type,
      user_details.id,
      access_token_indexhub_api
    );
    if (Object.keys(response).includes("ok")) {
      onClose();
      Toast(
        toast,
        "Credentials Stored",
        `Credentials for your ${source_type} source have been securely stored`,
        "success"
      );
      goToNextStep();
    } else {
      Toast(toast, "Error", response["detail"], "error");
    }
  };

  const submitSourcePath = async (configs: Record<string, string>) => {
    if (
      Object.keys(sources_schema[source_type]["variables"]).every((variable) =>
        Object.keys(configs).includes(variable)
      ) &&
      Object.keys(configs).includes("source_name")
    ) {
      let source_columns: Record<string, any> = []; // eslint-disable-line @typescript-eslint/no-explicit-any
      if (source_type == "s3") {
        source_columns = await getS3SourceColumns(
          configs["bucket_name"],
          configs["object_path"],
          configs["file_ext"],
          access_token_indexhub_api
        );
      }
      if (Object.keys(source_columns).includes("data")) {
        setSourceConfigs(configs);
        setSourceColumns(Object.keys(source_columns["data"]));
        goToNextStep();
      } else {
        Toast(toast, "Error", source_columns["detail"], "error");
      }
    } else {
      Toast(
        toast,
        "Empty / Invalid Columns",
        "Please ensure all required columns are filled with valid values",
        "error"
      );
    }
  };

  const submitSourceConfig = () => {
    if (time_col && freq && entity_cols && feature_cols) {
      goToNextStep();
    } else {
      Toast(
        toast,
        "Empty / Invalid Columns",
        "Please ensure all required columns are filled with valid values",
        "error"
      );
    }
  };

  const createSource = async () => {
    const create_source_response = await createSourceApi(
      user_details.id,
      source_configs["source_name"],
      freq,
      time_col,
      entity_cols,
      feature_cols,
      source_type,
      source_configs,
      "datetime_ftm_str",
      access_token_indexhub_api
    );
    if (Object.keys(create_source_response).includes("source_id")) {
      Toast(
        toast,
        "Preprocessing Source",
        "We will let you know when it's ready to create reports",
        "info"
      );
      navigate("/sources");
    } else {
      Toast(toast, "Error", create_source_response["detail"], "error");
    }
  };

  const stepScreens: Record<number, JSX.Element> = {
    0: (
      <SourceType
        sources_schema={sources_schema}
        submitSourceType={submitSourceType}
      />
    ),
    1: (
      <SourcePath
        source_type={source_type}
        sources_schema={sources_schema}
        goToPrevStep={goToPrevStep}
        submitSourcePath={submitSourcePath}
      />
    ),
    2: (
      <ConfigureSource
        column_options={column_options}
        submitSourceConfig={submitSourceConfig}
        goToPrevStep={goToPrevStep}
        setTimeCol={setTimeCol}
        setFreq={setFreq}
        setEntityCols={setEntityCols}
      />
    ),
    3: (
      <ConfirmCreateSource
        createSource={createSource}
        goToPrevStep={goToPrevStep}
        source_name={source_configs["source_name"]}
        s3_data_bucket={source_configs["bucket_name"]}
        raw_source_path={source_configs["object_path"]}
        freq={freq}
        time_col={time_col}
        feature_cols={feature_cols}
        entity_cols={entity_cols}
      />
    ),
  };

  return (
    <>
      <Text fontSize="2xl" fontWeight="bold" width="98%" textAlign="left">
        New Source
      </Text>
      <Container maxWidth="920px" py={{ base: "8", md: "16" }}>
        <Stack direction={{ base: "column", md: "row" }} spacing="4" mb="3rem">
          {steps.map((step, id) => (
            <Step
              key={id}
              title={step.title}
              description={step.description}
              isActive={currentStep === id}
              isCompleted={currentStep > id}
            />
          ))}
        </Stack>
        {stepScreens[currentStep]}
        <Modal isOpen={isOpen} onClose={onClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>
              <Text>Credentials</Text>
            </ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {source_type && (
                <SourceCredentials
                  required_credentials_schema={
                    sources_schema[source_type]["credentials"]
                  }
                  submitSourceCreds={submitSourceCreds}
                />
              )}
            </ModalBody>
          </ModalContent>
        </Modal>
      </Container>
    </>
  );
}
