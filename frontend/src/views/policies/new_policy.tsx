import React, { useState } from "react";
import { Container, Stack, useToast } from "@chakra-ui/react";
import { useEffect } from "react";
import { useAuth0AccessToken } from "../../utilities/hooks/auth0";
import { useSelector } from "react-redux";
import { AppState } from "../..";
import {
  getPoliciesSchema,
  createPolicy as createPolicyApi,
} from "../../utilities/backend_calls/policy";
import PolicyType from "./steps/policy_type";
import { Step } from "../../components/step";
import { useStep } from "../../utilities/hooks/useStep";
import PolicySource from "./steps/policy_source";
import Toast from "../../components/toast";
import PolicyConfigs from "./steps/policy_configs";
import ConfirmCreatePolicy from "./steps/confirm_create_policy";

const steps = [
  {
    title: "Step 1",
    description: "Your policy type",
  },
  {
    title: "Step 2",
    description: "Your policy sources",
  },
  {
    title: "Step 3",
    description: "Configure your policy",
  },
  {
    title: "Step 4",
    description: "Confirm source creation",
  },
];

const NewPolicy = () => {
  const [policies_schema, setPoliciesSchema] = useState<Record<any, any>>({}); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [policy_configs, setPolicyConfigs] = useState<Record<string, any>>({}); // eslint-disable-line @typescript-eslint/no-explicit-any
  const access_token_indexhub_api = useAuth0AccessToken();
  const [currentStep, { goToNextStep, goToPrevStep }] = useStep({
    maxStep: steps.length,
  });
  const toast = useToast();
  const user_details = useSelector((state: AppState) => state.reducer?.user);

  const submitPolicyType = (policy_type: string) => {
    policy_configs["policy_type"] = policy_type;
    setPolicyConfigs(policy_configs);
    goToNextStep();
  };

  const submitPolicySources = (policy_sources: Record<string, string>) => {
    if (Object.keys(policy_sources).includes("panel")) {
      policy_configs["panel"] = policy_sources["panel"];
      policy_configs["panel_name"] = policy_sources["panel_name"];
      policy_configs["baseline"] = policy_sources["baseline"]
        ? policy_sources["baseline"]
        : "";
      policy_configs["baseline_name"] = policy_sources["baseline_name"]
        ? policy_sources["baseline_name"]
        : "";
      policy_configs["inventory"] = policy_sources["inventory"]
        ? policy_sources["inventory"]
        : "";
      policy_configs["inventory_name"] = policy_sources["inventory_name"]
        ? policy_sources["inventory_name"]
        : "";
      policy_configs["transaction"] = policy_sources["transaction"]
        ? policy_sources["transaction"]
        : "";
      policy_configs["transaction_name"] = policy_sources["transaction_name"]
        ? policy_sources["transaction_name"]
        : "";
      setPolicyConfigs(policy_configs);
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

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const submitPolicyConfigs = (policy_configs: Record<string, any>) => {
    setPolicyConfigs(policy_configs);
    goToNextStep();
  };

  const createPolicy = async () => {
    const create_policy_response = await createPolicyApi(
      user_details.id,
      policy_configs,
      access_token_indexhub_api
    );
    if (Object.keys(create_policy_response).includes("policy_id")) {
      Toast(
        toast,
        "Policy Created",
        `Your new policy (${policy_configs["policy_name"]}) was successfuly created`,
        "success"
      );
      // navigate("/sources");
    } else {
      Toast(toast, "Error", create_policy_response["detail"], "error");
    }
  };

  const stepScreens: Record<number, JSX.Element> = {
    0: (
      <PolicyType
        policies_schema={policies_schema}
        submitPolicyType={submitPolicyType}
      />
    ),
    1: (
      <PolicySource
        policies_schema={policies_schema}
        policy_configs={policy_configs}
        submitPolicySources={submitPolicySources}
        goToPrevStep={goToPrevStep}
      />
    ),
    2: (
      <PolicyConfigs
        policies_schema={policies_schema}
        policy_configs={policy_configs}
        submitPolicyConfigs={submitPolicyConfigs}
        goToPrevStep={goToPrevStep}
      />
    ),
    3: (
      <ConfirmCreatePolicy
        policy_configs={policy_configs}
        createPolicy={createPolicy}
        goToPrevStep={goToPrevStep}
      />
    ),
  };

  useEffect(() => {
    const getPoliciesSchemaApi = async () => {
      const policies_schema = await getPoliciesSchema(
        user_details.id,
        access_token_indexhub_api
      );
      setPoliciesSchema(policies_schema);
    };
    if (access_token_indexhub_api && user_details.id) {
      getPoliciesSchemaApi();
    }
  }, [access_token_indexhub_api, user_details]);

  return (
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
    </Container>
  );
};

export default NewPolicy;
