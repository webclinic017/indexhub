import React from "react";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink } from "@chakra-ui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faChevronRight } from "@fortawesome/pro-light-svg-icons";
import { Link } from "react-router-dom";
import { capitalizeFirstLetter } from "../utilities/helpers";

const Breadcrumbs = (props: { current_path: string }) => {
  const paths = props.current_path.split("/");

  if (props.current_path != "/") {
    return (
      <Breadcrumb
        spacing="2"
        separator={<FontAwesomeIcon size="xs" icon={faChevronRight as any} />}
      >
        {paths.map((item, idx) => {
          if (idx > 0) {
            return (
              <BreadcrumbItem key={idx}>
                <BreadcrumbLink
                  as={Link}
                  to={`${paths.slice(0, idx + 1).join("/")}`}
                >
                  {capitalizeFirstLetter(item)}
                </BreadcrumbLink>
              </BreadcrumbItem>
            );
          }
        })}
      </Breadcrumb>
    );
  } else {
    return (
      <Breadcrumb
        spacing="2"
        separator={<FontAwesomeIcon size="xs" icon={faChevronRight as any} />}
      >
        <BreadcrumbItem isCurrentPage>
          <BreadcrumbLink as={Link} to="/">
            Home
          </BreadcrumbLink>
        </BreadcrumbItem>
      </Breadcrumb>
    );
  }
};

export default Breadcrumbs;
